from typing import List, Dict, Tuple
import logging
import copy
import re

from llm_interface import LLMHighlevelPlanner
from planner_interface import ClassicalPlannerInterface

class HybridPlanningCoordinator:
    def __init__(self, llm_planner: LLMHighlevelPlanner, classical_planner: ClassicalPlannerInterface):
        self.llm = llm_planner
        self.planner = classical_planner
        self.logger = logging.getLogger(__name__)

    def plan(self, natural_goal: str, domain_file: str, initial_state: Dict) -> Tuple[bool, List[str]]:
        """main planning loop combining LLM and classical planner"""
        
        # high-level planning & check
        domain_info = self._extract_domain_info(domain_file)
        subgoals = self.llm.decompose_goal(natural_goal, domain_info)
        subgoals = self.llm.resolve_conflicts(subgoals, initial_state)
        
        # Sequential low-level planning
        complete_plan = []
        current_state = initial_state.copy()
        
        for subgoal in subgoals:
            success, subplan = self._solve_subgoal_with_retry(
                domain_file, subgoal, current_state
            )
            
            if not success:
                self.logger.error(f"Failed to solve subgoal {subgoal['subgoal_id']}")
                return False, []
            
            complete_plan.extend(subplan)
            current_state = self._update_state_after_plan(current_state, subplan)
        
        return True, complete_plan
    
    def _solve_subgoal_with_retry(self,domain_file:str, subgoal:Dict, current_state: Dict, max_retries: int = 3) -> Tuple[bool, List[str]]:
        """solve with retry and llm adapt for additional tries"""
        for attempt in range(max_retries):
            success, plan = self.planner.solve_subgoal(domain_file, subgoal, current_state)
            
            if success:
                return True, plan
            
            # llm adapt the subgoal
            if attempt < max_retries - 1:
                error_info = f"Planning failed on attempt {attempt + 1}"
                adapted_subgoal = self.llm.adapt_plan(subgoal, error_info)
                subgoal = adapted_subgoal
        
        return False, []
    
    def _extract_domain_info(self, domain_file: str) -> str:
        """Extract human-readable domain information for LLM"""
        
        with open(domain_file, 'r') as f:
            pddl_content = f.read()
        
        # Parse pddl
        info = f"PDDL Domain File Content:\n{pddl_content}"
        return info
    

    def _update_state_after_plan(self, state: Dict, plan: List[str]) -> Dict:
        """Simulate plan execution to update blocks world state"""
                
        new_state = copy.deepcopy(state)
        
        for action_str in plan:
            # Parse action string formats:
            # "pickup a" or "(pickup a)" or "pickup(a)"
            action_str = action_str.strip().replace('(', ' ').replace(')', '').replace(',', ' ')
            parts = action_str.split()
            
            if len(parts) < 2:
                continue
                
            action_name = parts[0].lower()
            
            if action_name == "pickup":
                block = parts[1]
                self._apply_pickup(new_state, block)
                
            elif action_name == "putdown":
                block = parts[1]
                self._apply_putdown(new_state, block)
                
            elif action_name == "stack":
                block_a = parts[1] 
                block_b = parts[2]
                self._apply_stack(new_state, block_a, block_b)
                
            elif action_name == "unstack":
                block_a = parts[1]
                block_b = parts[2] 
                self._apply_unstack(new_state, block_a, block_b)
        
    def _validate_blocks_world_state(self, state: Dict) -> bool:
        """Validate that blocks world state is consistent"""
        
        # Check that each block is in exactly one place
        all_blocks = set()
        
        # Collect blocks from different predicates
        ontable_blocks = set(state.get("ontable", []))
        holding_blocks = set(state.get("holding", []))
        on_blocks_top = set(x for (x, y) in state.get("on", []))
        on_blocks_bottom = set(y for (x, y) in state.get("on", []))
        
        all_blocks.update(ontable_blocks)
        all_blocks.update(holding_blocks) 
        all_blocks.update(on_blocks_top)
        all_blocks.update(on_blocks_bottom)
        
        # Check no block is in multiple places
        for block in all_blocks:
            count = 0
            if block in ontable_blocks:
                count += 1
            if block in holding_blocks:
                count += 1
            if block in on_blocks_top:
                count += 1
            
            if count != 1:
                self.logger.error(f"Block {block} is in {count} places: ontable={block in ontable_blocks}, holding={block in holding_blocks}, on_top={block in on_blocks_top}")
                return False
        
        # Check clear predicate consistency
        clear_blocks = set(state.get("clear", []))
        
        # Blocks on table should be clear unless something is on them
        for block in ontable_blocks:
            if block not in on_blocks_bottom and block not in clear_blocks:
                self.logger.error(f"Block {block} on table but not clear and nothing on it")
                return False
        
        # Blocks on top of stacks should be clear
        for block in on_blocks_top:
            if block not in on_blocks_bottom and block not in clear_blocks:
                self.logger.error(f"Block {block} on top of stack but not clear")
                return False
        
        return True
    
    def _apply_pickup(self, state: Dict, block: str):
        """Apply pickup action effects"""
        # Preconditions: block is clear and on table, hand empty
        # Effects: block in hand, not on table, not clear
        
        # Remove from ontable
        if "ontable" in state and block in state["ontable"]:
            state["ontable"].remove(block)
        
        # Remove from clear
        if "clear" in state and block in state["clear"]:
            state["clear"].remove(block)
            
        # Add to holding (assuming single hand)
        state["holding"] = [block]
        
        # Remove handempty predicate
        if "handempty" in state:
            state["handempty"] = False
    
    def _apply_putdown(self, state: Dict, block: str):
        """Apply putdown action effects"""
        # Preconditions: holding block
        # Effects: block on table, block clear, hand empty
        
        # Remove from holding
        if "holding" in state and block in state["holding"]:
            state["holding"].remove(block)
            
        # Add to ontable
        if "ontable" not in state:
            state["ontable"] = []
        state["ontable"].append(block)
        
        # Add to clear
        if "clear" not in state:
            state["clear"] = []
        state["clear"].append(block)
        
        # Set hand empty
        state["handempty"] = True
    
    def _apply_stack(self, state: Dict, block_a: str, block_b: str):
        """Apply stack action effects"""
        # Preconditions: holding block_a, block_b is clear
        # Effects: block_a on block_b, block_a clear, block_b not clear, hand empty
        
        # Remove block_a from holding
        if "holding" in state and block_a in state["holding"]:
            state["holding"].remove(block_a)
            
        # Remove block_b from clear
        if "clear" in state and block_b in state["clear"]:
            state["clear"].remove(block_b)
            
        # Add (block_a, block_b) to on relation
        if "on" not in state:
            state["on"] = []
        state["on"].append((block_a, block_b))
        
        # Add block_a to clear
        if "clear" not in state:
            state["clear"] = []
        state["clear"].append(block_a)
        
        # Set hand empty
        state["handempty"] = True
    
    def _apply_unstack(self, state: Dict, block_a: str, block_b: str):
        """Apply unstack action effects"""
        # Preconditions: block_a on block_b, block_a clear, hand empty
        # Effects: holding block_a, block_b clear, not on relation
        
        # Remove (block_a, block_b) from on relation
        if "on" in state:
            state["on"] = [(x, y) for (x, y) in state["on"] if not (x == block_a and y == block_b)]
            
        # Remove block_a from clear
        if "clear" in state and block_a in state["clear"]:
            state["clear"].remove(block_a)
            
        # Add block_b to clear
        if "clear" not in state:
            state["clear"] = []
        state["clear"].append(block_b)
        
        # Add block_a to holding
        state["holding"] = [block_a]
        
        # Set hand not empty
        state["handempty"] = False
