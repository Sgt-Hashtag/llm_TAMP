from llm_interface import LLMHighlevelPlanner
from planner_interface import ClassicalPlannerInterface  
from hybrid_coordinator import HybridPlanningCoordinator
import os

def test_simple_stacking():
    """Test simple 3-block stacking scenario"""
    
    # Initialize components
    llm_planner = LLMHighlevelPlanner()
    classical_planner = ClassicalPlannerInterface()
    coordinator = HybridPlanningCoordinator(llm_planner, classical_planner)
    
    # Define blocks world scenario
    natural_goal = "Stack blocks A, B, and C in that order from bottom to top"
    
    domain_file = "domain_models/blocks_world.pddl"
    
    # Initial state: all blocks on table
    initial_state = {
        "ontable": ["a", "b", "c"],
        "clear": ["a", "b", "c"],
        "holding": [],
        "handempty": True,
        "on": []
    }
    
    print("=== Simple Stacking Test ===")
    print(f"Goal: {natural_goal}")
    print(f"Initial state: {initial_state}")
    
    # Execute hybrid planning
    success, plan = coordinator.plan(natural_goal, domain_file, initial_state)
    
    if success:
        print(f"\nPlan found ({len(plan)} actions):")
        for i, action in enumerate(plan):
            print(f"{i+1}. {action}")
        
        # Simulate final state
        final_state = coordinator._update_state_after_plan(initial_state, plan)
        print(f"\nFinal state: {final_state}")
        
        # Validate final state
        if coordinator._validate_blocks_world_state(final_state):
            print("✓ Final state is valid!")
        else:
            print("✗ Final state is invalid!")
            
        return True
    else:
        print("✗ Planning failed")
        return False

def test_complex_rearrangement():
    """Test complex rearrangement scenario"""
    
    llm_planner = LLMHighlevelPlanner()
    classical_planner = ClassicalPlannerInterface()
    coordinator = HybridPlanningCoordinator(llm_planner, classical_planner)
    
    natural_goal = "Rearrange the blocks so that A is on B, B is on C, and D is on the table next to the stack"
    
    domain_file = "domain_models/blocks_world.pddl"
    
    # Initial state: A on C, B on D, all clear on top
    initial_state = {
        "ontable": ["c", "d"],
        "clear": ["a", "b"],
        "holding": [],
        "handempty": True,
        "on": [("a", "c"), ("b", "d")]
    }
    
    print("\n=== Complex Rearrangement Test ===")
    print(f"Goal: {natural_goal}")
    print(f"Initial state: {initial_state}")
    
    success, plan = coordinator.plan(natural_goal, domain_file, initial_state)
    
    if success:
        print(f"\nPlan found ({len(plan)} actions):")
        for i, action in enumerate(plan):
            print(f"{i+1}. {action}")
        
        final_state = coordinator._update_state_after_plan(initial_state, plan)
        print(f"\nFinal state: {final_state}")
        
        if coordinator._validate_blocks_world_state(final_state):
            print("✓ Final state is valid!")
        else:
            print("✗ Final state is invalid!")
            
        return True
    else:
        print("✗ Planning failed")
        return False

def test_tower_building():
    """Test building a tower with many blocks"""
    
    llm_planner = LLMHighlevelPlanner()
    classical_planner = ClassicalPlannerInterface()
    coordinator = HybridPlanningCoordinator(llm_planner, classical_planner)
    
    natural_goal = "Build a tower with blocks in alphabetical order: A at bottom, then B, then C, then D, then E at top"
    
    domain_file = "domain_models/blocks_world.pddl"
    
    # Initial state: 5 blocks scattered
    initial_state = {
        "ontable": ["a", "b", "c", "d", "e"],
        "clear": ["a", "b", "c", "d", "e"],
        "holding": [],
        "handempty": True,
        "on": []
    }
    
    print("\n=== Tower Building Test ===")
    print(f"Goal: {natural_goal}")
    print(f"Initial state: {initial_state}")
    
    success, plan = coordinator.plan(natural_goal, domain_file, initial_state)
    
    if success:
        print(f"\nPlan found ({len(plan)} actions):")
        for i, action in enumerate(plan):
            print(f"{i+1}. {action}")
        
        final_state = coordinator._update_state_after_plan(initial_state, plan)
        print(f"\nFinal state: {final_state}")
        
        if coordinator._validate_blocks_world_state(final_state):
            print("✓ Final state is valid!")
            
            # Check if tower is built correctly
            expected_on = [("b", "a"), ("c", "b"), ("d", "c"), ("e", "d")]
            actual_on = final_state.get("on", [])
            
            if all(relation in actual_on for relation in expected_on):
                print("✓ Tower built correctly!")
            else:
                print("✗ Tower not built as expected")
                print(f"Expected: {expected_on}")
                print(f"Actual: {actual_on}")
        else:
            print("✗ Final state is invalid!")
            
        return True
    else:
        print("✗ Planning failed")
        return False

def run_all_tests():
    """Run all blocks world tests"""
    
    print("Running Blocks World Hybrid Planning Tests...\n")
    
    # Check if domain file exists
    domain_file = "domain_models/blocks_world.pddl"
    if not os.path.exists(domain_file):
        print(f"Warning: Domain file {domain_file} not found!")
        print("Make sure to create the domain file first.")
        return
    
    tests = [
        test_simple_stacking,
        test_complex_rearrangement,
        test_tower_building
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append(False)
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("All passed!")
    else:
        print("Not passed.")

if __name__ == "__main__":
    run_all_tests()