import operator
from typing import Annotated, List, TypedDict, Union
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

# --- 1. STATE DEFINITION ---
# This is the "Memory" passed between agents.
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    requirement: str           # The user's original request
    plan: str                  # The Architect's technical spec
    code: str                  # The Python code generated
    test_results: str          # Output from the Sandbox execution
    auditor_feedback: str      # Notes on bugs/security/finance logic
    iteration_count: int       # To prevent infinite loops

# --- 2. AGENT DEFINITIONS (THE NODES) ---

# Initialize LLM (Switch to GPT-4o or Claude 3.5 via API)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def architect_node(state: AgentState):
    """
    Role: Breaks down the trading requirement into a technical spec.
    """
    print(f"--- [ARCHITECT] Planning: {state['requirement']} ---")
    
    prompt = f"""
    You are a Senior System Architect for a High-Frequency Trading Platform.
    Analyze the user requirement: '{state['requirement']}'
    
    Create a step-by-step technical implementation plan.
    Focus on: Data structures, modularity, and error handling.
    Do not write code yet, just the plan.
    """
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"plan": response.content, "iteration_count": state.get("iteration_count", 0)}

def developer_node(state: AgentState):
    """
    Role: Writes the Python code based on the plan and previous feedback.
    """
    print("--- [DEVELOPER] Writing Code ---")
    
    # Context includes the plan AND any feedback from the Auditor/Executor
    context = f"""
    Plan: {state['plan']}
    Previous Feedback (if any): {state.get('auditor_feedback', 'None')}
    Test Results (if any): {state.get('test_results', 'None')}
    """
    
    prompt = f"""
    You are a Senior Python Developer for a Quant Fund.
    Write the Python code to satisfy the Plan.
    
    CRITICAL RULES:
    1. Use 'Decimal' for all currency calculations. Never use floats.
    2. Include comments explaining the logic.
    3. Return ONLY the python code block.
    
    Context:
    {context}
    """
    response = llm.invoke([SystemMessage(content=prompt)])
    # In a real app, you would parse the code block out of the markdown
    return {"code": response.content, "iteration_count": state["iteration_count"] + 1}

def executor_node(state: AgentState):
    """
    Role: The Sandbox. Tries to run the code to check for syntax errors.
    NOTE: In production, this connects to Docker/E2B. Here we simulate it.
    """
    print("--- [EXECUTOR] Running inside Sandbox ---")
    
    code = state['code']
    
    # SIMULATION of a sandbox run
    # If the code contains "float", we simulate a failure to force a retry
    if "float" in code and "Decimal" not in code:
        result = "ERROR: runtime_error: Precision loss detected. Use Decimal."
    else:
        result = "SUCCESS: Code compiled and ran verification tests."
        
    return {"test_results": result}

def auditor_node(state: AgentState):
    """
    Role: The Financial Guardrail. Checks for Logic & Security.
    """
    print("--- [AUDITOR] Reviewing Code ---")
    
    prompt = f"""
    You are a Quant Auditor. Review the following code for Trading Systems.
    
    Check for:
    1. Look-ahead Bias (using future data).
    2. Floating point errors (using float instead of Decimal).
    3. Lack of Stop-Loss mechanisms.
    
    Code:
    {state['code']}
    
    Test Results:
    {state['test_results']}
    
    If the code is good, reply 'APPROVED'.
    If bad, reply with specific feedback on what to fix.
    """
    response = llm.invoke([SystemMessage(content=prompt)])
    return {"auditor_feedback": response.content}

# --- 3. CONDITIONAL LOGIC (THE EDGES) ---

def router(state: AgentState):
    """
    Decides the next step:
    - If Approved -> End
    - If Rejected -> Back to Developer
    - If too many retries -> End (Failed)
    """
    feedback = state['auditor_feedback']
    count = state['iteration_count']
    
    if "APPROVED" in feedback.upper():
        return "human_review"
    elif count > 3:
        return "failed"
    else:
        return "developer"

# --- 4. BUILD THE GRAPH ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("architect", architect_node)
workflow.add_node("developer", developer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("auditor", auditor_node)

# Add Edges
workflow.set_entry_point("architect")
workflow.add_edge("architect", "developer")
workflow.add_edge("developer", "executor")
workflow.add_edge("executor", "auditor")

# Add Conditional Edge
workflow.add_conditional_edges(
    "auditor",
    router,
    {
        "developer": "developer",   # Loop back to fix bugs
        "human_review": END,        # Success
        "failed": END               # Give up
    }
)

# Compile
app = workflow.compile()

# --- 5. EXECUTION EXAMPLE ---

if __name__ == "__main__":
    user_request = "Create a Momentum Trading function that buys if the 50-day MA crosses above the 200-day MA."
    
    inputs = {"requirement": user_request, "iteration_count": 0}
    
    print(f"Starting Factory with Request: {user_request}\n")
    
    # Run the graph
    for output in app.stream(inputs):
        for key, value in output.items():
            # This prints the flow as it happens
            print(f"Finished Node: {key}")
