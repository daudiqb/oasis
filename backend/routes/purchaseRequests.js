const express = require("express");
const { pool } = require("../db");

const router = express.Router();

// POST /api/purchase-requests - send a request to buy a listing
router.post("/", async (req, res, next) => {
    try {
        const { listing_id, buyer_id, message } = req.body;

        if (!listing_id || !buyer_id) {
            return res.status(400).json({ error: "listing_id and buyer_id are required" });
        }

        const listing = await pool.query(
            `SELECT seller_id, status FROM listings WHERE id = $1`,
            [listing_id]
        );
        if (listing.rows.length === 0) {
            return res.status(404).json({ error: "listing not found" });
        }
        if (listing.rows[0].seller_id === Number(buyer_id)) {
            return res.status(400).json({ error: "you cannot request your own listing" });
        }
        if (listing.rows[0].status !== "available") {
            return res.status(400).json({ error: "listing is not available" });
        }

        const result = await pool.query(
            `INSERT INTO purchase_requests (listing_id, buyer_id, message)
             VALUES ($1, $2, $3)
             RETURNING *`,
            [listing_id, buyer_id, message || null]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        next(err);
    }
});

// GET /api/purchase-requests - view outgoing (buyer_id) or incoming (seller_id) requests
router.get("/", async (req, res, next) => {
    try {
        const { buyer_id, seller_id, status } = req.query;

        if (!buyer_id && !seller_id) {
            return res.status(400).json({ error: "buyer_id or seller_id is required" });
        }

        const conditions = [];
        const values = [];

        if (buyer_id) {
            values.push(buyer_id);
            conditions.push(`pr.buyer_id = $${values.length}`);
        }
        if (seller_id) {
            values.push(seller_id);
            conditions.push(`l.seller_id = $${values.length}`);
        }
        if (status) {
            values.push(status);
            conditions.push(`pr.status = $${values.length}`);
        }

        const result = await pool.query(
            `SELECT pr.*, l.title AS listing_title, l.price AS listing_price, l.seller_id
             FROM purchase_requests pr
             JOIN listings l ON l.id = pr.listing_id
             WHERE ${conditions.join(" AND ")}
             ORDER BY pr.created_at DESC`,
            values
        );
        res.json(result.rows);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
