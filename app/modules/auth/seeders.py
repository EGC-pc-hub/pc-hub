from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):

        # Seeding users
        desired = [
            ("user1@example.com", "1234"),
            ("user2@example.com", "1234"),
        ]

        # Make seeding idempotent: reuse existing users when present
        new_users = []
        existing = {}
        for email, password in desired:
            u = User.query.filter_by(email=email).first()
            if u:
                existing[email] = u
            else:
                new_users.append(User(email=email, password=password))

        created = []
        if new_users:
            created = self.seed(new_users)

        # Merge created users into existing map
        for u in created:
            existing[u.email] = u

        # Preserve order
        seeded_users = [existing[email] for email, _ in desired]

        # Create profiles for each user inserted.
        user_profiles = []
        names = [("John", "Doe"), ("Jane", "Doe")]

        for user, name in zip(seeded_users, names):
            # Only create a profile if it doesn't already exist
            existing_profile = UserProfile.query.filter_by(user_id=user.id).first()
            if existing_profile:
                continue

            profile_data = {
                "user_id": user.id,
                "orcid": "",
                "affiliation": "Some University",
                "name": name[0],
                "surname": name[1],
            }
            user_profile = UserProfile(**profile_data)
            user_profiles.append(user_profile)

        # Seeding user profiles (if any)
        if user_profiles:
            self.seed(user_profiles)
