#!/usr/bin/env python3
"""
Category and Subcategory Seeder Script
Populates the database with predefined categories and subcategories based on bank transaction patterns.
"""

import sys
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from core.database import Base, engine, Session, Category, Subcategory


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created/verified")


def seed_categories_and_subcategories():
    """Seed the database with categories and subcategories."""
    session = Session()

    try:
        # Define categories with their subcategories
        categories_data = {
            "Food & Dining": [
                "Restaurants",
                "Fast Food",
                "Coffee & Beverages",
                "Groceries & Supermarkets",
                "Street Food",
                "Bakery & Snacks"
            ],
            "Shopping": [
                "Online Shopping",
                "Retail Stores",
                "Convenience Stores",
                "Pharmacy",
                "Electronics",
                "Clothing & Fashion"
            ],
            "Transportation": [
                "Public Transport",
                "Taxi & Ride Sharing",
                "Fuel",
                "Parking",
                "Vehicle Maintenance"
            ],
            "Health & Fitness": [
                "Gym & Fitness",
                "Medical Expenses",
                "Pharmacy",
                "Health Insurance"
            ],
            "Entertainment": [
                "Movies & Recreation",
                "Games & Apps",
                "Books & Media",
                "Sports & Activities"
            ],
            "Personal Care": [
                "Haircut & Grooming",
                "Beauty & Cosmetics",
                "Spa & Wellness"
            ],
            "Bills & Utilities": [
                "Bank Fees",
                "Service Charges",
                "Subscription Services",
                "Insurance"
            ],
            "Transfers & Banking": [
                "Bank Transfers",
                "ATM Withdrawals",
                "Cash Deposits",
                "Investment Transfers"
            ],
            "Income": [
                "Salary",
                "Freelance Income",
                "Investment Returns",
                "Other Income"
            ],
            "Education": [
                "Tuition Fees",
                "Books & Supplies",
                "Online Courses",
                "Educational Services"
            ],
            "Travel": [
                "Accommodation",
                "Transportation",
                "Food & Dining",
                "Souvenirs & Shopping"
            ]
        }

        print("Starting category and subcategory seeding...")

        for category_name, subcategory_names in categories_data.items():
            # Create or get category
            category = session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.flush()  # Flush to get the ID
                print(f"✓ Created category: {category_name}")
            else:
                print(f"→ Category already exists: {category_name}")

            # Create subcategories
            for subcategory_name in subcategory_names:
                subcategory = session.query(Subcategory).filter_by(
                    name=subcategory_name,
                    category_id=category.id
                ).first()

                if not subcategory:
                    subcategory = Subcategory(
                        name=subcategory_name,
                        category_id=category.id
                    )
                    session.add(subcategory)
                    print(f"  ✓ Created subcategory: {subcategory_name}")
                else:
                    print(f"  → Subcategory already exists: {subcategory_name}")

        session.commit()
        print("\n✅ All categories and subcategories have been seeded successfully!")

        # Print summary
        total_categories = session.query(Category).count()
        total_subcategories = session.query(Subcategory).count()
        print(f"📊 Summary: {total_categories} categories, {total_subcategories} subcategories")

    except IntegrityError as e:
        session.rollback()
        print(f"❌ Integrity error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        session.rollback()
        print(f"❌ An error occurred: {e}")
        sys.exit(1)
    finally:
        session.close()


def display_seeded_data():
    """Display all seeded categories and subcategories."""
    session = Session()

    try:
        print("\n" + "=" * 60)
        print("SEEDED CATEGORIES AND SUBCATEGORIES")
        print("=" * 60)

        categories = session.query(Category).order_by(Category.name).all()

        for category in categories:
            print(f"\n📁 {category.name} (ID: {category.id})")
            subcategories = session.query(Subcategory).filter_by(
                category_id=category.id
            ).order_by(Subcategory.name).all()

            for subcategory in subcategories:
                print(f"   └── {subcategory.name} (ID: {subcategory.id})")

    except Exception as e:
        print(f"❌ Error displaying data: {e}")
    finally:
        session.close()


def main():
    """Main function to run the seeder."""
    print("🌱 Category and Subcategory Seeder")
    print("=" * 40)

    # Create tables
    create_tables()

    # Seed data
    seed_categories_and_subcategories()

    # Display results
    display_seeded_data()

    print(f"\n🎉 Seeding completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()