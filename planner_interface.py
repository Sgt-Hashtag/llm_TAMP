from unified_planning.shortcuts import *
from unified_planning.io import PDDLReader
import tempfile
import os
from typing import Dict,Tuple

class ClassicalPlannerInterface:
    def __init__(self, planner_name="pyperplan"):
        self.planner_name = planner_name

    def _create_problem_file(self, domain_file: str, subgoal: Dict, current_state: Dict) -> str:
        """ generates PDDL problem file from subgoal specification"""
        
        domain_name = self._extract_domain_name(domain_file)
        
        problem_content = f"""
        (define (problem subgoal-{subgoal['subgoal_id']})
            (:domain {domain_name})
            
            (:objects
                {self._format_objects(subgoal['resources_needed'])}
            )
            
            (:init
                {self._format_initial_state(current_state)}
            )
            
            (:goal
                {subgoal['formal_goal']}
            )
        )
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.pddl', delete=False) as f:
            f.write(problem_content)
            return f.name
    
    def solve_subgoal(self, domain_file: str, subgoal: Dict, current_state: Dict) -> Tuple[bool, List[str]]:
        """Solves a single subgoal using classical planning"""
        
        problem_file = self._create_problem_file(domain_file, subgoal, current_state)
        
        try:
            reader = PDDLReader()
            problem = reader.parse_problem(domain_file, problem_file)
            
            with OneshotPlanner(name=self.planner_name) as planner:
                result = planner.solve(problem)
                
            if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
                print(f"{planner.name} found this plan: {result.plan}")
                plan_actions = [str(action) for action in result.plan.actions]
                return True, plan_actions
            else:
                print("No plan found.")
                return False, []
                
        except Exception as e:
            return False, [f"Planning error: {str(e)}"]
        
        finally:
            if os.path.exists(problem_file):
                os.remove(problem_file)

    def validate_plan(self, domain_file: str, problem_file: str, plan: List[str]) -> bool:
        """Validate that a plan actually achieves the goal"""
        
        try:
            reader = PDDLReader()
            problem = reader.parse_problem(domain_file, problem_file)
            
            current_state = problem.initial_values
            
            for action_str in plan:
                action = self._parse_action(action_str)
                current_state = self._apply_action(action, current_state)
            #checking satification
            return problem.goals.is_satisfied(current_state)
            
        except Exception:
            return False