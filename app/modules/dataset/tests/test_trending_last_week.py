import uuid
from datetime import datetime, timezone, timedelta

from app import db
from app.modules.dataset.models import DataSet, DSMetaData, Author, DSDownloadRecord, PublicationType
from app.modules.auth.models import User
from app.modules.dataset.services import DataSetService


def create_dataset_with_author(title, user_id, author_name):
    dsmeta = DSMetaData(title=title, description="desc", publication_type=PublicationType.NONE)
    author = Author(name=author_name)
    dsmeta.authors.append(author)
    dataset = DataSet(user_id=user_id, ds_meta_data=dsmeta)
    db.session.add(dsmeta)
    db.session.add(dataset)
    db.session.flush()
    return dataset


def create_download(dataset_id, days_ago=0):
    download = DSDownloadRecord(
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        download_cookie=str(uuid.uuid4()),
    )
    db.session.add(download)


def test_trending_datasets_last_week(clean_database, test_app):
    # create a user
    user = User(email="u@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # create datasets
    ds1 = create_dataset_with_author("DS One", user.id, "Author One")
    ds2 = create_dataset_with_author("DS Two", user.id, "Author Two")
    ds3 = create_dataset_with_author("DS Three", user.id, "Author Three")
    ds4 = create_dataset_with_author("DS Old", user.id, "Author Old")

    db.session.commit()

    # create downloads placed explicitly inside the previous calendar week
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(days=now.weekday())
    last_week_start = start_of_week - timedelta(days=7)

    # place records on last_week_start + 1, +2, +3 days
    for _ in range(5):
        rec = DSDownloadRecord(dataset_id=ds1.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4()))
        db.session.add(rec)
    for _ in range(3):
        rec = DSDownloadRecord(dataset_id=ds2.id, download_date=last_week_start + timedelta(days=2), download_cookie=str(uuid.uuid4()))
        db.session.add(rec)
    for _ in range(2):
        rec = DSDownloadRecord(dataset_id=ds3.id, download_date=last_week_start + timedelta(days=3), download_cookie=str(uuid.uuid4()))
        db.session.add(rec)
    # ds4 older than last week
    for _ in range(10):
        rec = DSDownloadRecord(dataset_id=ds4.id, download_date=last_week_start - timedelta(days=10), download_cookie=str(uuid.uuid4()))
        db.session.add(rec)

    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)

    # expect ds1, ds2, ds3 in that order
    assert len(trending) == 3
    assert trending[0]["id"] == ds1.id
    assert trending[0]["downloads"] == 5
    assert trending[1]["id"] == ds2.id
    assert trending[1]["downloads"] == 3
    assert trending[2]["id"] == ds3.id
    assert trending[2]["downloads"] == 2


def test_trending_last_week_no_downloads(clean_database, test_app):
    """If there are no downloads last week, the service should return an empty list."""
    user = User(email="no@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    # create datasets but no downloads
    create_dataset_with_author("A", user.id, "Author A")
    create_dataset_with_author("B", user.id, "Author B")
    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)
    assert trending == []


def test_trending_last_week_ties(clean_database, test_app):
    """When two datasets have the same count, both should appear with the correct counts."""
    user = User(email="tie@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    ds1 = create_dataset_with_author("Tie1", user.id, "T1")
    ds2 = create_dataset_with_author("Tie2", user.id, "T2")
    db.session.commit()

    # place 3 downloads for each in last week
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(days=now.weekday())
    last_week_start = start_of_week - timedelta(days=7)

    for _ in range(3):
        db.session.add(DSDownloadRecord(dataset_id=ds1.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())))
        db.session.add(DSDownloadRecord(dataset_id=ds2.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())))

    db.session.commit()

    service = DataSetService()
    trending = service.trending_datasets_last_week(limit=3)
    assert len(trending) == 2
    ids = {t['id'] for t in trending}
    assert ids == {ds1.id, ds2.id}
    for t in trending:
        assert t['downloads'] == 3


def test_api_trending_returns_json(test_client, clean_database, test_app):
    """API should return JSON list consistent with the service."""
    user = User(email="api@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    ds1 = create_dataset_with_author("API1", user.id, "A1")
    db.session.commit()

    # add one download in last week
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    start_of_week = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc) - timedelta(days=now.weekday())
    last_week_start = start_of_week - timedelta(days=7)
    db.session.add(DSDownloadRecord(dataset_id=ds1.id, download_date=last_week_start + timedelta(days=1), download_cookie=str(uuid.uuid4())))
    db.session.commit()

    resp = test_client.get('/dataset/api/trending')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]['id'] == ds1.id
    assert data[0]['downloads'] == 1
