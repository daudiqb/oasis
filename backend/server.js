const express = require("express");
const listingsRouter = require("./routes/listings");

const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

app.get("/api/health", (req, res) => {
    res.json({ status : "ok"});
});

app.use("/api/listings", listingsRouter);

app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ error: "internal server error" });
});

// Checking if the backend is up
app.listen(PORT, () => {
    console.log(`Backend running on http://localhost:${PORT}`);
});