import  openai
from typing import List,Dict,Literal,Tuple
import json

class LLMHighlevelPlanner:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.client = openai.OpenAI()

    def decompose_goal(self, natural_goal: str, domain_info: str) -> List[Dict]:
        """Decompose high-level goal into structured subgoals via use of prompts
            direct openai api calls
        """
        
        prompt = f"""
        Domain: {domain_info}
        
        High-level goal: {natural_goal}
        
        Decompose this into a sequence of concrete subgoals. Each subgoal should be:
        1. Specific and measurable
        2. Achievable by low-level planning
        3. Ordered logically
        
        Return as JSON list with structure:
        [
            {{
                "subgoal_id": 1,
                "description": "human readable description",
                "formal_goal": "PDDL-style goal condition",
                "prerequisites": ["list of conditions that must be true"],
                "resources_needed": ["list of required objects/agents"]
            }}
        ]
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        
        except json.JSONDecodeError:
            return self._fallback_parse(response.choices[0].message.content)
        
    
    def resolve_conflicts(self, subgoals: List[Dict], current_state: Dict) -> List[Dict]:
        """resolve conflicts between subgoals"""
        
        prompt = f"""
        Current world state: {current_state}
        Planned subgoals: {json.dumps(subgoals, indent=2)}
        
        Analyze for potential conflicts:
        1. Resource conflicts (same object needed simultaneously)
        2. Prerequisite violations (subgoal B needs result of subgoal A)
        3. State conflicts (subgoals that undo each other)
        
        Return revised subgoal sequence resolving any conflicts.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        
        except json.JSONDecodeError:
            return self._fallback_parse(response.choices[0].message.content)
         

    def adapt_plan(self, failed_subgoal: Dict, error_info: str) -> Dict:
        """Adapt plan when low-level planning fails"""
        
        prompt = f"""
        Failed subgoal: {failed_subgoal}
        Error: {error_info}
        
        Suggest adaptation:
        1. Alternative approach to same subgoal
        2. Modified subgoal that's more achievable
        3. Additional prerequisite subgoals needed
        
        Return adapted subgoal in same JSON format.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            message=[{"role":"user", "content":"prompt"}],
            temperature=0.2
        )

        try:
            return json.loads(response.choices[0].message.content)

        except json.JSONDecodeError:
            return self._fallback_parse(response.choices[0].message.content)

