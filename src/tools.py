def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """Mock API function to capture a lead's information."""
    # Print exactly as required by the assignment
    print(f"\n[SYSTEM] Lead captured successfully: {name}, {email}, {platform}")
    
    return "Lead successfully captured on the backend."
