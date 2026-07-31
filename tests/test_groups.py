import uuid


def test_create_group(client):
    resp = client.post("/api/groups", json={"name": "Ski trip"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ski trip"
    assert uuid.UUID(body["id"])

    listing = client.get("/api/groups").json()
    assert any(g["name"] == "Ski trip" for g in listing)


def test_blank_group_name_rejected(client):
    resp = client.post("/api/groups", json={"name": "   "})
    assert resp.status_code == 422


def test_add_member(client, group_with_members):
    group_id = group_with_members(["Ana"])
    detail = client.get(f"/api/groups/{group_id}").json()
    assert [m["name"] for m in detail["members"]] == ["Ana"]


def test_duplicate_member_rejected(client, group_with_members):
    group_id = group_with_members(["Ana"])
    resp = client.post(f"/api/groups/{group_id}/members", json={"name": "ana"})
    assert resp.status_code == 422
    assert "already in this group" in resp.json()["detail"]


def test_unknown_group_404(client):
    assert client.get(f"/api/groups/{uuid.uuid4()}").status_code == 404


def test_malformed_group_id_rejected_before_lookup(client):
    resp = client.get("/api/groups/not-a-uuid")
    assert resp.status_code == 422
