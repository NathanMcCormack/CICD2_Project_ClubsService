import pytest

@pytest.fixture(autouse=True)
def _mock_user_service(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "verify_user_exists", lambda user_id: None)

def club_payload(
    name="ATU Badminton Club",
    description="Weekly badminton training and matches.",
    category="club",
    cost=20,
):
    return {"name": name, "description": description, "category": category, "membership_cost": cost}

def membership_payload(user_id=1, club_id=1):
    return {"user_id": user_id, "club_id": club_id}

def create_club(client, **kwargs):
    r = client.post("/api/clubs", json=club_payload(**kwargs))
    assert r.status_code == 201
    return r.json()

def test_list_memberships_empty_ok(client):
    r = client.get("/api/memberships")
    assert r.status_code == 200
    assert r.json() == []

def test_create_membership_club_missing_404(client):
    r = client.post("/api/memberships", json=membership_payload(user_id=1, club_id=999999))
    assert r.status_code == 404
    assert "club not found" in r.json()["detail"].lower()

def test_create_membership_ok_includes_club(client):
    club = create_club(
        client,
        name="ATU Hiking Club",
        description="Weekend hikes around Connemara.",
        category="club",
        cost=10,
    )
    r = client.post("/api/memberships", json=membership_payload(user_id=42, club_id=club["id"]))
    assert r.status_code == 201
    body = r.json()

    assert "id" in body
    assert body["user_id"] == 42
    assert body["club_id"] == club["id"]
    assert "club" in body
    assert body["club"]["id"] == club["id"]
    assert body["club"]["name"] == "ATU Hiking Club"

def test_duplicate_membership_conflict_409(client):
    club = create_club(
        client,
        name="ATU Chess Society",
        description="Friendly chess games every Friday.",
        category="society",
        cost=5,
    )

    r1 = client.post("/api/memberships", json=membership_payload(user_id=7, club_id=club["id"]))
    assert r1.status_code == 201

    r2 = client.post("/api/memberships", json=membership_payload(user_id=7, club_id=club["id"]))
    assert r2.status_code == 409
    assert "already a member" in r2.json()["detail"].lower()

def test_patch_membership_ok_change_user_id(client):
    club = create_club(
        client,
        name="ATU Robotics Club",
        description="Build and program robots together.",
        category="club",
        cost=30,
    )
    created = client.post("/api/memberships", json=membership_payload(user_id=10, club_id=club["id"])).json()
    mid = created["id"]

    r = client.patch(f"/api/memberships/{mid}", json={"user_id": 11})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == mid
    assert body["user_id"] == 11
    assert body["club_id"] == club["id"]
    assert body["club"]["name"] == "ATU Robotics Club"

def test_patch_membership_ok_change_club_id(client):
    c1 = create_club(client, name="ATU Film Club", description="Weekly screenings and discussions.", category="club", cost=5)
    c2 = create_club(client, name="ATU Music Club", description="Jam sessions and live performances.", category="club", cost=15)

    m = client.post("/api/memberships", json=membership_payload(user_id=99, club_id=c1["id"])).json()

    r = client.patch(f"/api/memberships/{m['id']}", json={"club_id": c2["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["club_id"] == c2["id"]
    assert body["club"]["id"] == c2["id"]
    assert body["club"]["name"] == "ATU Music Club"

def test_patch_membership_404(client):
    r = client.patch("/api/memberships/999999", json={"user_id": 2})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

def test_patch_membership_new_club_missing_404(client):
    club = create_club(
        client,
        name="ATU Art Club",
        description="Painting and drawing workshops weekly.",
        category="club",
        cost=12,
    )
    m = client.post("/api/memberships", json=membership_payload(user_id=5, club_id=club["id"])).json()

    r = client.patch(f"/api/memberships/{m['id']}", json={"club_id": 999999})
    assert r.status_code == 404
    assert "club not found" in r.json()["detail"].lower()

def test_delete_membership_then_404(client):
    club = create_club(
        client,
        name="ATU Swimming Club",
        description="Pool training every Tuesday.",
        category="club",
        cost=10,
    )
    m = client.post("/api/memberships", json=membership_payload(user_id=55, club_id=club["id"])).json()
    mid = m["id"]

    r1 = client.delete(f"/api/memberships/{mid}")
    assert r1.status_code == 204

    r2 = client.delete(f"/api/memberships/{mid}")
    assert r2.status_code == 404
    assert "not found" in r2.json()["detail"].lower()

def test_delete_club_cascades_memberships(client):
    club = create_club(
        client,
        name="ATU Rowing Club",
        description="Rowing sessions and river training.",
        category="club",
        cost=20,
    )
    m = client.post("/api/memberships", json=membership_payload(user_id=1, club_id=club["id"])).json()

    r_del = client.delete(f"/api/clubs/{club['id']}")
    assert r_del.status_code == 204

    # Membership should no longer exist due to ORM cascade on ClubDB.memberships
    r_patch = client.patch(f"/api/memberships/{m['id']}", json={"user_id": 2})
    assert r_patch.status_code == 404
