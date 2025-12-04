import os
import shutil
from datetime import datetime, timezone

from dotenv import load_dotenv

from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):

    priority = 2  # Lower priority

    def run(self):
        # Retrieve users
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # Create exactly one dataset per JSON file in pc_examples
        datasets_dir = os.path.join(os.path.dirname(__file__), "pc_examples")
        dataset_files = [f for f in os.listdir(datasets_dir) if f.endswith(".json")]

        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "pc_examples")

        seeded_datasets = []
        for idx, dataset_file in enumerate(dataset_files):
            # Use minimal metrics since JSONs are component catalogs
            ds_metrics = DSMetrics(number_of_models="1", number_of_features="0")
            seeded_ds_metrics = self.seed([ds_metrics])[0]

            ds_meta_data = DSMetaData(
                deposition_id=idx + 1,
                title=os.path.splitext(dataset_file)[0],
                description=f"Dataset generated from {dataset_file}",
                publication_type=PublicationType.SOFTWARE,
                publication_doi=f"10.1234/dataset{idx + 1}",
                dataset_doi=f"10.1234/dataset{idx + 1}",
                tags="pc_examples",
                ds_metrics_id=seeded_ds_metrics.id,
            )
            self.seed([ds_meta_data])

            # Authors for dataset metadata
            authors = [
                Author(
                    name=f"Author {i + 1}",
                    affiliation=f"Affiliation {i + 1}",
                    orcid=f"0000-0000-0000-000{i}",
                    ds_meta_data_id=ds_meta_data.id,
                )
                for i in range(2)
            ]
            self.seed(authors)

            # Create one DataSet for this file, alternate owners
            dataset_model = DataSet(
                user_id=user1.id if idx % 2 == 0 else user2.id,
                ds_meta_data_id=ds_meta_data.id,
                created_at=datetime.now(timezone.utc),
            )
            seeded_dataset = self.seed([dataset_model])[0]
            seeded_datasets.append(seeded_dataset)

            # Create FMMetaData and FeatureModel for this dataset file
            fm_meta = FMMetaData(
                uvl_filename=dataset_file,
                title=f"Feature Model {idx + 1}",
                description=f"Feature model from {dataset_file}",
                publication_type=PublicationType.HARDWARE,
                publication_doi=f"10.1234/fm{idx + 1}",
                tags="pc_examples",
                uvl_version="1.0",
            )
            fm_meta = self.seed([fm_meta])[0]

            # Author for FMMetaData
            fm_author = Author(
                name=f"Author {idx + 5}",
                affiliation=f"Affiliation {idx + 5}",
                orcid=f"0000-0000-0000-00{idx + 5}",
                fm_meta_data_id=fm_meta.id,
            )
            self.seed([fm_author])

            feature_model = FeatureModel(data_set_id=seeded_dataset.id, fm_meta_data_id=fm_meta.id)
            feature_model = self.seed([feature_model])[0]

            # Copy file and create Hubfile entry
            user_id = seeded_dataset.user_id
            dest_folder = os.path.join(
                working_dir,
                "uploads",
                f"user_{user_id}",
                f"dataset_{seeded_dataset.id}",
            )
            os.makedirs(dest_folder, exist_ok=True)
            src_path = os.path.join(src_folder, dataset_file)
            dest_path = os.path.join(dest_folder, dataset_file)
            shutil.copy(src_path, dest_folder)

            hubfile = Hubfile(
                name=dataset_file,
                checksum=f"checksum{idx + 1}",
                size=os.path.getsize(dest_path),
                feature_model_id=feature_model.id,
            )
            self.seed([hubfile])
