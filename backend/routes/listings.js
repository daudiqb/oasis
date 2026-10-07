const express = require("express");
const { pool } = require("../db");

const router = express.Router();

// GET /api/listings - browse/search listings
router.get("/", async (req, res, next) => {
    try {
        const { search, category, status, seller_id } = req.query;
        const conditions = [];
        const values = [];

        if (search) {
            values.push(`%${search}%`);
            conditions.push(`title ILIKE $${values.length}`);
        }
        if (category) {
            values.push(category);
            conditions.push(`category = $${values.length}`);
        }
        if (status) {
            values.push(status);
            conditions.push(`status = $${values.length}`);
        }
        if (seller_id) {
            values.push(seller_id);
            conditions.push(`seller_id = $${values.length}`);
        }

        const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
        const result = await pool.query(
            `SELECT * FROM listings ${where} ORDER BY created_at DESC`,
            values
        );
        res.json(result.rows);
    } catch (err) {
        next(err);
    }
});

// POST /api/listings - create a listing
router.post("/", async (req, res, next) => {
    try {
        const { seller_id, title, description, price, category, item_condition } = req.body;

        if (!seller_id || !title || price === undefined) {
            return res.status(400).json({ error: "seller_id, title, and price are required" });
        }
        if (typeof price !== "number" || price < 0) {
            return res.status(400).json({ error: "price must be a non-negative number" });
        }

        const result = await pool.query(
            `INSERT INTO listings (seller_id, title, description, price, category, item_condition)
             VALUES ($1, $2, $3, $4, $5, $6)
             RETURNING *`,
            [seller_id, title, description || null, price, category || null, item_condition || null]
        );
        res.status(201).json(result.rows[0]);
    } catch (err) {
        next(err);
    }
});

module.exports = router;
