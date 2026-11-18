const API_BASE = "/api";

// The Flask endpoints wrap their payload in these keys.
const LISTINGS_KEY = "Listings";
const LISTING_KEY = "Listing";

async function handleResponse(res) {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      // flask-restx reports the reason in `message`
      if (body.message) message = body.message;
    } catch {
      // response had no JSON body
    }
    throw new Error(message);
  }
  return res.json();
}

export function getListings() {
  return fetch(`${API_BASE}/listings`)
    .then(handleResponse)
    .then((body) => body[LISTINGS_KEY]);
}

export function createListing(data) {
  return fetch(`${API_BASE}/listings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then(handleResponse)
    .then((body) => body[LISTING_KEY]);
}
