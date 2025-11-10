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

        # Create or reuse DSMetrics instance
        ds_metrics = DSMetrics.query.filter_by(number_of_models="5", number_of_features="50").first()
        if not ds_metrics:
            ds_metrics = DSMetrics(number_of_models="5", number_of_features="50")
            ds_metrics = self.seed([ds_metrics])[0]

        # Create DSMetaData instances (only if not exist by deposition_id)
        seeded_ds_meta_data = []
        to_create_ds_meta = []
        for i in range(4):
            deposition_id = 1 + i
            existing = DSMetaData.query.filter_by(deposition_id=deposition_id).first()
            if existing:
                seeded_ds_meta_data.append(existing)
            else:
                to_create_ds_meta.append(
                    DSMetaData(
                        deposition_id=deposition_id,
                        title=f"Sample dataset {i+1}",
                        description=f"Description for dataset {i+1}",
                        publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                        publication_doi=f"10.1234/dataset{i+1}",
                        dataset_doi=f"10.1234/dataset{i+1}",
                        tags="tag1, tag2",
                        ds_metrics_id=ds_metrics.id,
                    )
                )
        if to_create_ds_meta:
            created = self.seed(to_create_ds_meta)
            seeded_ds_meta_data.extend(created)

        # Create Author instances and associate with DSMetaData (ensure unique per name + ds_meta_data_id)
        for i in range(4):
            ds_meta = seeded_ds_meta_data[i % 4]
            name = f"Author {i+1}"
            existing_author = Author.query.filter_by(name=name, ds_meta_data_id=ds_meta.id).first()
            if not existing_author:
                author = Author(
                    name=name,
                    affiliation=f"Affiliation {i+1}",
                    orcid=f"0000-0000-0000-000{i}",
                    ds_meta_data_id=ds_meta.id,
                )
                self.seed([author])

        # Create DataSet instances (unique by user_id + ds_meta_data_id)
        datasets = []
        for i in range(4):
            user_id = user1.id if i % 2 == 0 else user2.id
            ds_meta_id = seeded_ds_meta_data[i].id
            existing_ds = DataSet.query.filter_by(user_id=user_id, ds_meta_data_id=ds_meta_id).first()
            if not existing_ds:
                datasets.append(
                    DataSet(
                        user_id=user_id,
                        ds_meta_data_id=ds_meta_id,
                        created_at=datetime.now(timezone.utc),
                    )
                )
        seeded_datasets = []
        if datasets:
            seeded_datasets = self.seed(datasets)
        else:
            # load existing datasets used for feature models
            # assume at least the required ones exist
            for i in range(4):
                user_id = user1.id if i % 2 == 0 else user2.id
                ds_meta_id = seeded_ds_meta_data[i].id
                ds = DataSet.query.filter_by(user_id=user_id, ds_meta_data_id=ds_meta_id).first()
                if ds:
                    seeded_datasets.append(ds)

        # FMMetaData: create or reuse by uvl_filename
        seeded_fm_meta_data = []
        to_create_fm = []
        for i in range(12):
            filename = f"file{i+1}.uvl"
            existing = FMMetaData.query.filter_by(uvl_filename=filename).first()
            if existing:
                seeded_fm_meta_data.append(existing)
            else:
                to_create_fm.append(
                    FMMetaData(
                        uvl_filename=filename,
                        title=f"Feature Model {i+1}",
                        description=f"Description for feature model {i+1}",
                        publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                        publication_doi=f"10.1234/fm{i+1}",
                        tags="tag1, tag2",
                        uvl_version="1.0",
                    )
                )
        if to_create_fm:
            created_fm = self.seed(to_create_fm)
            seeded_fm_meta_data.extend(created_fm)

        # Create FM Authors (unique by name + fm_meta_data_id)
        for i in range(12):
            fm_meta = seeded_fm_meta_data[i]
            name = f"Author {i+5}"
            existing_author = Author.query.filter_by(name=name, fm_meta_data_id=fm_meta.id).first()
            if not existing_author:
                fm_author = Author(
                    name=name,
                    affiliation=f"Affiliation {i+5}",
                    orcid=f"0000-0000-0000-000{i+5}",
                    fm_meta_data_id=fm_meta.id,
                )
                self.seed([fm_author])

        # FeatureModel: create if not exists by data_set_id + fm_meta_data_id
        seeded_feature_models = []
        to_create_fm_models = []
        for i in range(12):
            data_set_id = seeded_datasets[i // 3].id
            fm_meta_id = seeded_fm_meta_data[i].id
            existing_fm = FeatureModel.query.filter_by(data_set_id=data_set_id, fm_meta_data_id=fm_meta_id).first()
            if existing_fm:
                seeded_feature_models.append(existing_fm)
            else:
                to_create_fm_models.append(FeatureModel(data_set_id=data_set_id, fm_meta_data_id=fm_meta_id))
        if to_create_fm_models:
            created_models = self.seed(to_create_fm_models)
            seeded_feature_models.extend(created_models)

        # Create files, associate them with FeatureModels and copy files if Hubfile not present
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "uvl_examples")
        for i in range(12):
            file_name = f"file{i+1}.uvl"
            feature_model = seeded_feature_models[i]
            dataset = next(ds for ds in seeded_datasets if ds.id == feature_model.data_set_id)
            user_id = dataset.user_id

            # skip if hubfile already exists for this feature_model and name
            existing_hub = Hubfile.query.filter_by(name=file_name, feature_model_id=feature_model.id).first()
            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)
            file_src = os.path.join(src_folder, file_name)
            file_path = os.path.join(dest_folder, file_name)

            if not existing_hub:
                # copy source only if exists and destination missing or different
                if os.path.exists(file_src) and (not os.path.exists(file_path)):
                    shutil.copy(file_src, dest_folder)

                # create hubfile entry
                size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                uvl_file = Hubfile(
                    name=file_name,
                    checksum=f"checksum{i+1}",
                    size=size,
                    feature_model_id=feature_model.id,
                )
                self.seed([uvl_file])
