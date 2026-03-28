import os
import django
import random
from datetime import timedelta

# Setup Django environment — MUST come before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fsm_backend.settings")
django.setup()

from django.utils import timezone
from jobs.models import Job


def generate_jobs(num_jobs=150):
    print("Starting job generation...")

    # Clear existing jobs
    deleted_count, _ = Job.objects.all().delete()
    print(f"Deleted {deleted_count} existing jobs from the database.")

    # 1. Realistic job data pools
    service_types = [
        "HVAC Maintenance",
        "AC Repair",
        "Plumbing Leak",
        "Electrical Inspection",
        "Appliance Installation",
        "Roof Repair",
        "Network Setup",
        "Painting Job",
        "Smart Home Installation",
        "Boiler Servicing",
    ]

    cities = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Dallas",
        "Denver",
    ]
    streets = [
        "Oak St",
        "Pine St",
        "Maple Ave",
        "Cedar Ln",
        "Elm St",
        "Washington Blvd",
        "Sunset Blvd",
    ]

    priorities = ["low", "medium", "high"]
    currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "KES"]

    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Sarah", "Thomas", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

    # 3. Create the jobs
    jobs_created = 0
    for i in range(num_jobs):
        service = random.choice(service_types)

        # Random start time in the next 1 to 30 days (all jobs are future / not overdue)
        start_time = timezone.now() + timedelta(
            days=random.randint(1, 30),
            hours=random.randint(8, 16),  # Between 8 AM and 4 PM
            minutes=random.choice([0, 15, 30, 45]),
        )

        # End time is 1 to 4 hours after start time
        end_time = start_time + timedelta(hours=random.randint(1, 4))

        # Generate realistic phone number (10 digits)
        phone_number = f"555{random.randint(1000000, 9999999)}"

        # Valid JSON address object
        address = {
            "street": f"{random.randint(100, 9999)} {random.choice(streets)}",
            "city": random.choice(cities),
            "state": "NY",
            "zip": f"{random.randint(10000, 99999)}",
            "LatLong": {
                "latitude": round(random.uniform(25.0, 49.0), 6),
                "longitude": round(random.uniform(-125.0, -67.0), 6),
            },
        }

        requirements = {
            "tools": ["Standard Toolkit", "Ladder"]
            if "Repair" in service
            else ["Inspection Kit"],
            "notes": f"Customer requests a call 30 mins before arrival. Routine {service.lower()}.",
        }

        price = round(random.uniform(50.0, 1000.0), 2)
        currency = random.choice(currencies)
        customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"

        Job.objects.create(
            title=f"{service} #{random.randint(1000, 9999)}",
            description=f"Client reported issues requiring {service.lower()}. Please bring requested tools and check in upon arrival.",
            customer_name=customer_name,
            price=price,
            currency=currency,
            status="unassigned",
            priority=random.choice(priorities),
            phone_number=phone_number,
            address=address,
            start_time=start_time,
            end_time=end_time,
            requirements=requirements,
        )
        jobs_created += 1

    print(f"Successfully generated {jobs_created} unassigned, non-overdue jobs!")


if __name__ == "__main__":
    generate_jobs(150)
