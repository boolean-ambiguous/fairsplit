def test_create_group(client):
    resp = client.post("/groups", data={"name": "Ski trip"})
    assert resp.status_code == 200
    assert "Ski trip" in client.get("/groups").text


def test_blank_group_name_rejected(client):
    resp = client.post("/groups", data={"name": "   "})
    assert resp.status_code == 422


def test_add_member(client, group_with_members):
    group_id = group_with_members(["Ana"])
    page = client.get(f"/groups/{group_id}")
    assert "Ana" in page.text


def test_duplicate_member_rejected(client, group_with_members):
    group_id = group_with_members(["Ana"])
    resp = client.post(f"/groups/{group_id}/members", data={"name": "ana"})
    assert resp.status_code == 422
    assert "already in this group" in resp.text


def test_unknown_group_404(client):
    assert client.get("/groups/999").status_code == 404
