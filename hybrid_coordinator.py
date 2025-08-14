from typing import List, Dict, Tuple
import logging

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
        """Simulate plan execution to update world state"""
        
        # This is domain-specific - you'd need to implement
        # action simulation for your specific domain
        
        new_state = state.copy()
        
        for action in plan:
            # Apply action effects to state
            # Implementation depends on your domain representation
            pass
        
        return new_state
    
