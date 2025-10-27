#!/usr/bin/env python3
"""
Quick pet lookup using the existing Database class
"""

from database import Database

def main():
    print("🐾 Accessing Pet Database...")
    
    # Initialize database
    db = Database()
    
    # You'll need a pet_id - let's check what's in the database
    # Since there's no get_all_pets method, we'll query directly
    import sqlite3
    
    conn = sqlite3.connect("chewy_journey.db")
    cursor = conn.cursor()
    
    # Get all pet IDs and names
    cursor.execute("SELECT id, name, species, breed, age_months FROM pets ORDER BY rowid DESC")
    pets = cursor.fetchall()
    conn.close()
    
    if not pets:
        print("❌ No pets found in database")
        return
    
    print(f"\n📊 Found {len(pets)} pet(s):")
    print("=" * 50)
    
    for i, (pet_id, name, species, breed, age_months) in enumerate(pets, 1):
        print(f"{i}. {name} (ID: {pet_id})")
        print(f"   {species} - {breed} - {age_months} months")
        print()
    
    # Get the latest pet (first in the list since we ordered by rowid DESC)
    latest_pet_id = pets[0][0]
    print(f"🎯 Getting full profile for latest pet: {pets[0][1]} (ID: {latest_pet_id})")
    
    # Use the existing database method
    pet_profile = db.get_pet(latest_pet_id)
    
    if pet_profile:
        print("\n✅ Latest Pet Profile:")
        print("=" * 50)
        print(f"🐕 Name: {pet_profile.name}")
        print(f"🏷️  Species: {pet_profile.species}")
        print(f"🐾 Breed: {pet_profile.breed}")
        print(f"📅 Age: {pet_profile.ageMonths} months")
        print(f"👤 Gender: {pet_profile.gender}")
        print(f"🏠 Household: {pet_profile.householdType}")
        print(f"🌳 Yard Access: {pet_profile.yardAccess}")
        print(f"📍 Zip Code: {pet_profile.zipCode}")
        print(f"⚖️ Weight: {pet_profile.weightLbs} lbs")
        print(f"📏 Height: {pet_profile.heightAtShoulderInches} inches")
        print(f"🦴 Chew Strength: {pet_profile.chewStrength}")
        print(f"⚡ Activity Level: {pet_profile.activityLevel}")
        print(f"🚫 Allergies: {pet_profile.allergies}")
        print(f"📝 About: {pet_profile.about}")
        print(f"👁️ Appearance: {pet_profile.appearance}")
        print(f"💰 Budget: {pet_profile.budgetBand}")
        print(f"🏷️ Brand Preferences: {pet_profile.brandPreferences}")
        
        # Return the pet profile object for use in other scripts
        return pet_profile
    else:
        print("❌ Could not retrieve pet profile")
        return None

if __name__ == "__main__":
    latest_pet = main()
