from src.database import insert_lead

def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """Mock API function to capture a lead's information and save it to SQLite database."""
    # Safely insert into the real database
    insert_lead(name, email, platform)
    
    # Print securely into the terminal loop
    print(f"\n[SYSTEM] Lead captured safely to DB: {name}, {email}, {platform}")
    
    return "Lead successfully captured on the backend Database."
