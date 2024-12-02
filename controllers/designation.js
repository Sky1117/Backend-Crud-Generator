const express = require('express');
const router = express.Router();
const Designation = require('../models/Designation');


// CRUD operations for Designation

// Create
router.post('/designation',  async (req, res) => {
    
    const newDesignation = new Designation(req.body);
    try {
        const savedDesignation = await newDesignation.save();
        res.status(200).json(savedDesignation);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Bulk Upload
router.post('/designation/bulk-upload', upload.single('file'), async (req, res) => {
    const file = req.file;
    if (!file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    try {
        const data = await parseExcel(file.path);
        const bulkInsertResult = await Designation.insertMany(data);
        res.status(200).json(bulkInsertResult);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Read all with pagination
router.get('/designation', async (req, res) => {
    
const page = parseInt(req.query.page) || 1;
const limit = parseInt(req.query.limit) || 10;
const skip = (page - 1) * limit;

    try {
        const designation = await Designation.find().skip(skip).limit(limit);
        res.status(200).json(designation);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Read one
router.get('/designation/:id', async (req, res) => {
    try {
        const designation = await Designation.findById(req.params.id);
        if (!designation) {
            return res.status(404).json("The designation was not found.");
        }
        res.status(200).json(designation);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Update
router.put('/designation/:id',  async (req, res) => {
    
    try {
        const updatedDesignation = await Designation.findByIdAndUpdate(
            req.params.id,
            { $set: req.body },
            { new: true }
        );
        if (!updatedDesignation) {
            return res.status(404).json("The designation was not found.");
        }
        res.status(200).json(updatedDesignation);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Delete
router.delete('/designation/:id', async (req, res) => {
    try {
        const deletedDesignation = await Designation.findByIdAndDelete(req.params.id);
        if (!deletedDesignation) {
            return res.status(404).json("The designation was not found.");
        }
        res.status(200).json("The designation has been deleted.");
    } catch (err) {
        res.status(500).json(err);
    }
});

// Search with pagination and validation
router.get('/designation/search', async (req, res) => {
    const query = {};
    let hasValidQuery = false;
    const validFields = new Set(["name", "reportTo", "permission"]);
    const invalidFields = [];

    Object.keys(req.query).forEach(key => {
        if (validFields.has(key)) {
            query[key] = req.query[key];
            hasValidQuery = true;
        } else {
            invalidFields.push(key);
        }
    });

    if (!hasValidQuery) {
        return res.status(400).json({
            error: "No valid search parameters provided.",
            invalidParameters: invalidFields
        });
    }

    
const page = parseInt(req.query.page) || 1;
const limit = parseInt(req.query.limit) || 10;
const skip = (page - 1) * limit;

    try {
        const results = await Designation.find(query).skip(skip).limit(limit);
        if (!results.length) {
            return res.status(404).json({ error: "No results found for the given query." });
        }
        res.status(200).json(results);
    } catch (err) {
        res.status(500).json(err);
    }
});

// Download report
router.get('/designation/report', async (req, res) => {
    const { startDate, endDate } = req.query;

    // Validate startDate and endDate format or values if necessary

    try {
        const reportData = await Designation.find({
            createdAt: {
                $gte: new Date(startDate),
                $lte: new Date(endDate)
            }
        });

        if (!reportData.length) {
            return res.status(404).json({ error: "No data found for the given dates." });
        }

        // Convert reportData to Excel format using a library like pandas or openpyxl
        // Example using pandas:
        report_df = pd.DataFrame(reportData)
        report_path = './downloads/report.xlsx'
        report_df.to_excel(report_path, index=False)

        // Provide the download link
        res.download(report_path, 'report.xlsx', (err) => {
            if (err) {
                // Handle error if download fails
                res.status(500).json({ error: "Failed to download the report." });
            }

            // Clean up: delete the temporary file
            fs.unlinkSync(report_path);
        });
    } catch (err) {
        res.status(500).json(err);
    }
});

module.exports = router;