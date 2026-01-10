import pytest

def club_payload(
    name="ATU Badminton Club",
    description="Weekly badminton training and matches.",
    category="club",
    cost=20,
):
    return {
        "name": name,
        "description": description,
        "category": category,
        "membership_cost": cost,
    }

def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "clubs"}

def test_list_clubs_empty_ok(client):
    r = client.get("/api/clubs")
    assert r.status_code == 200
    assert r.json() == []

def test_create_club_ok(client):
    r = client.post("/api/clubs", json=club_payload())
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == "ATU Badminton Club"
    assert data["category"] == "club"
    assert data["membership_cost"] == 20

def test_list_clubs_after_create_ok(client):
    client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Chess Society",
            description="Friendly chess games every Friday.",
            category="society",
            cost=5,
        ),
    )
    client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Hiking Club",
            description="Weekend hikes around Connemara.",
            category="club",
            cost=10,
        ),
    )

    r = client.get("/api/clubs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 2
    assert r.json()[0]["name"] == "ATU Chess Society"

def test_get_club_by_id_ok(client):
    created = client.post("/api/clubs", json=club_payload()).json()
    cid = created["id"]

    r = client.get(f"/api/clubs/{cid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == cid
    assert body["name"] == "ATU Badminton Club"

def test_get_club_by_id_404(client):
    r = client.get("/api/clubs/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

def test_duplicate_name_conflict_409(client):
    client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Robotics Club",
            description="Build and program robots together.",
            category="club",
            cost=30,
        ),
    )
    r = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Robotics Club",
            description="Different description but same name.",
            category="club",
            cost=25,
        ),
    )
    assert r.status_code == 409
    assert "already exist" in r.json()["detail"].lower() or "duplicate" in r.json()["detail"].lower()

def test_duplicate_description_conflict_409(client):
    client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Music Club",
            description="Jam sessions and live performances.",
            category="club",
            cost=15,
        ),
    )
    r = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Drama Club",
            description="Jam sessions and live performances.",
            category="society",
            cost=12,
        ),
    )
    assert r.status_code == 409
    assert "already exist" in r.json()["detail"].lower() or "duplicate" in r.json()["detail"].lower()

def test_patch_club_ok(client):
    created = client.post("/api/clubs", json=club_payload()).json()
    cid = created["id"]

    r = client.patch(f"/api/clubs/{cid}", json={"membership_cost": 25})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == cid
    assert body["membership_cost"] == 25

def test_patch_club_404(client):
    r = client.patch("/api/clubs/999999", json={"membership_cost": 25})
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

def test_patch_club_conflict_409(client):
    c1 = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Swimming Club",
            description="Pool training every Tuesday.",
            category="club",
            cost=10,
        ),
    ).json()
    c2 = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Running Club",
            description="Track sessions and 5k runs.",
            category="club",
            cost=8,
        ),
    ).json()

    r = client.patch(f"/api/clubs/{c2['id']}", json={"name": c1["name"]})
    assert r.status_code == 409
    assert "duplicate" in r.json()["detail"].lower() or "failed" in r.json()["detail"].lower()

def test_put_replace_club_ok(client):
    created = client.post("/api/clubs", json=club_payload()).json()
    cid = created["id"]

    updated = club_payload(
        name="ATU Coding Society",
        description="Workshops and hack nights for coding.",
        category="society",
        cost=0,
    )
    r = client.put(f"/api/clubs/{cid}", json=updated)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == cid
    assert body["name"] == "ATU Coding Society"
    assert body["category"] == "society"
    assert body["membership_cost"] == 0

def test_put_missing_club_404(client):
    r = client.put("/api/clubs/999999", json=club_payload())
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

def test_put_conflict_409(client):
    c1 = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Film Club",
            description="Weekly screenings and discussions.",
            category="club",
            cost=5,
        ),
    ).json()
    c2 = client.post(
        "/api/clubs",
        json=club_payload(
            name="ATU Photography Club",
            description="Photo walks and editing tips.",
            category="club",
            cost=5,
        ),
    ).json()

    updated = club_payload(
        name=c1["name"],  # duplicate name
        description="New description long enough.",
        category="club",
        cost=12,
    )
    r = client.put(f"/api/clubs/{c2['id']}", json=updated)
    assert r.status_code == 409
    assert "duplicate" in r.json()["detail"].lower() or "failed" in r.json()["detail"].lower()

def test_delete_club_then_404(client):
    created = client.post("/api/clubs", json=club_payload()).json()
    cid = created["id"]

    r1 = client.delete(f"/api/clubs/{cid}")
    assert r1.status_code == 204

    r2 = client.delete(f"/api/clubs/{cid}")
    assert r2.status_code == 404
    assert "not found" in r2.json()["detail"].lower()

# --- 422 validation tests (schema-driven) ---
@pytest.mark.parametrize("bad_category", ["team", "societies", "Club", "", "123"])
def test_create_club_bad_category_422(client, bad_category):
    r = client.post(
        "/api/clubs",
        json=club_payload(
            category=bad_category,
            name="ATU Rowing Club",
            description="Rowing sessions and river training.",
            cost=20,
        ),
    )
    assert r.status_code == 422

@pytest.mark.parametrize("bad_cost", [-1, 151])
def test_create_club_bad_membership_cost_422(client, bad_cost):
    r = client.post(
        "/api/clubs",
        json=club_payload(
            cost=bad_cost,
            name="ATU Table Tennis Club",
            description="Table tennis practice each week.",
            category="club",
        ),
    )
    assert r.status_code == 422

@pytest.mark.parametrize("bad_name", ["AB", "", "  "])
def test_create_club_bad_name_422(client, bad_name):
    r = client.post(
        "/api/clubs",
        json=club_payload(
            name=bad_name,
            description="Valid description with enough length.",
            category="club",
            cost=10,
        ),
    )
    assert r.status_code == 422

@pytest.mark.parametrize("bad_desc", ["Too short", "", "123456789"])
def test_create_club_bad_description_422(client, bad_desc):
    r = client.post("/api/clubs", json=club_payload(name="ATU Art Club", description=bad_desc, category="club", cost=10))
    assert r.status_code == 422
