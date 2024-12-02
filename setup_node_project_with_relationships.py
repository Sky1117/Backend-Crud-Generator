import os
import json
import pandas as pd

# Function to read Excel file and return structured data
def read_excel(file_path):
    df = pd.read_excel(file_path)
    models = {}
    for _, row in df.iterrows():
        model_name = row['Model']
        if model_name not in models:
            models[model_name] = []
        models[model_name].append({
            'column': row['Column'],
            'datatype': row['Datatype'],
            'depends_on_model': row['Depends on Model'],
            'modal_column': row['Modal Column']
        })
    return models

# Function to generate model files with relationships based on depends_on_model and modal_column
def generate_model_files(models):
    data_type_mapping = {
        'String': 'String',
        'Number': 'Number',
        'Boolean': 'Boolean',
        'Date': 'Date',
        'Array': '[String]',  # Adjust if array type needs to be different
        # Add more data types as needed
    }

    for model, columns in models.items():
        with open(f'./models/{model.lower()}.js', 'w') as file:
            file.write('const mongoose = require(\'mongoose\');\n')
            file.write(f'const {model}Schema = new mongoose.Schema({{\n')
            
            for col in columns:
                if col['datatype'] == 'autogenerated Object':
                    continue  # Assuming _id is autogenerated

                if pd.notna(col['depends_on_model']) and pd.notna(col['modal_column']):
                    # Handling relationship only if both depends_on_model and modal_column are defined
                    ref_model = col['depends_on_model']
                    file.write(f'    {col["column"]}: {{ type: mongoose.Schema.Types.ObjectId, ref: \'{ref_model}\' }},\n')
                else:
                    # Use specified data type
                    data_type = data_type_mapping.get(col['datatype'], 'String')  # Default to String if datatype not found
                    file.write(f'    {col["column"]}: {{ type: {data_type} }},\n')

            # Adding created_by and is_active fields to every model schema
            file.write('    created_by: { type: mongoose.Schema.Types.ObjectId, ref: \'User\' },\n')
            file.write('    is_active: { type: Boolean, default: true },\n')
            file.write(f'}}, {{ timestamps: true }});\n')  # Add timestamps option here
            file.write(f'module.exports = mongoose.model(\'{model}\', {model}Schema);\n')

# Function to parse Excel file and return data
def parse_excel(file_path):
    df = pd.read_excel(file_path)
    data = df.to_dict(orient='records')
    return data

# Function to generate CRUD operations for a model
def generate_crud_operations(model, columns, has_attachments):
    pagination_code = '''
const page = parseInt(req.query.page) || 1;
const limit = parseInt(req.query.limit) || 10;
const skip = (page - 1) * limit;
'''

    upload_handler = f'''
const upload = require('../middleware/upload');
const handleAttachments = (req) => {{
    if (!req.files) return;
    req.body.attachments = req.files.map(file => file.path);
}};
''' if has_attachments else ''

    upload_param = 'upload.array(\'attachments\'),' if has_attachments else ''

    search_fields = [col['column'] for col in columns if col['column'] != 'attachments']
    search_fields_json = json.dumps(search_fields)

    crud_operations = f'''
const express = require('express');
const router = express.Router();
const {model} = require('../models/{model}');
{upload_handler}

// CRUD operations for {model}

// Create
router.post('/{model.lower()}', {upload_param} async (req, res) => {{
    {f'handleAttachments(req);' if has_attachments else ''}
    const new{model} = new {model}(req.body);
    try {{
        const saved{model} = await new{model}.save();
        res.status(200).json(saved{model});
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Bulk Upload
router.post('/{model.lower()}/bulk-upload', upload.single('file'), async (req, res) => {{
    const file = req.file;
    if (!file) {{
        return res.status(400).json({{ error: 'No file uploaded' }});
    }}

    try {{
        const data = await parseExcel(file.path);
        const bulkInsertResult = await {model}.insertMany(data);
        res.status(200).json(bulkInsertResult);
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Read all with pagination
router.get('/{model.lower()}', async (req, res) => {{
    {pagination_code}
    try {{
        const {model.lower()} = await {model}.find().skip(skip).limit(limit);
        res.status(200).json({model.lower()});
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Read one
router.get('/{model.lower()}/:id', async (req, res) => {{
    try {{
        const {model.lower()} = await {model}.findById(req.params.id);
        if (!{model.lower()}) {{
            return res.status(404).json("The {model.lower()} was not found.");
        }}
        res.status(200).json({model.lower()});
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Update
router.put('/{model.lower()}/:id', {upload_param} async (req, res) => {{
    {f'handleAttachments(req);' if has_attachments else ''}
    try {{
        const updated{model} = await {model}.findByIdAndUpdate(
            req.params.id,
            {{ $set: req.body }},
            {{ new: true }}
        );
        if (!updated{model}) {{
            return res.status(404).json("The {model.lower()} was not found.");
        }}
        res.status(200).json(updated{model});
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Delete
router.delete('/{model.lower()}/:id', async (req, res) => {{
    try {{
        const deleted{model} = await {model}.findByIdAndDelete(req.params.id);
        if (!deleted{model}) {{
            return res.status(404).json("The {model.lower()} was not found.");
        }}
        res.status(200).json("The {model.lower()} has been deleted.");
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Search with pagination and validation
router.get('/{model.lower()}/search', async (req, res) => {{
    const query = {{}};
    let hasValidQuery = false;
    const validFields = new Set({search_fields_json});
    const invalidFields = [];

    Object.keys(req.query).forEach(key => {{
        if (validFields.has(key)) {{
            query[key] = req.query[key];
            hasValidQuery = true;
        }} else {{
            invalidFields.push(key);
        }}
    }});

    if (!hasValidQuery) {{
        return res.status(400).json({{
            error: "No valid search parameters provided.",
            invalidParameters: invalidFields
        }});
    }}

    {pagination_code}
    try {{
        const results = await {model}.find(query).skip(skip).limit(limit);
        if (!results.length) {{
            return res.status(404).json({{ error: "No results found for the given query." }});
        }}
        res.status(200).json(results);
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

// Download report
router.get('/{model.lower()}/report', async (req, res) => {{
    const {{ startDate, endDate }} = req.query;

    // Validate startDate and endDate format or values if necessary

    try {{
        const reportData = await {model}.find({{
            createdAt: {{
                $gte: new Date(startDate),
                $lte: new Date(endDate)
            }}
        }});

        if (!reportData.length) {{
            return res.status(404).json({{ error: "No data found for the given dates." }});
        }}

        // Convert reportData to Excel format using a library like pandas or openpyxl
        // Example using pandas:
        report_df = pd.DataFrame(reportData)
        report_path = './downloads/report.xlsx'
        report_df.to_excel(report_path, index=False)

        // Provide the download link
        res.download(report_path, 'report.xlsx', (err) => {{
            if (err) {{
                // Handle error if download fails
                res.status(500).json({{ error: "Failed to download the report." }});
            }}

            // Clean up: delete the temporary file
            fs.unlinkSync(report_path);
        }});
    }} catch (err) {{
        res.status(500).json(err);
    }}
}});

module.exports = router;
'''
    return crud_operations.strip()

# Function to generate controller files with CRUD operations and download report
def generate_controller_files(models):
    for model, columns in models.items():
        has_attachments = any(col['column'] == 'attachments' for col in columns)
        with open(f'./controllers/{model.lower()}.js', 'w') as file:
            file.write(generate_crud_operations(model, columns, has_attachments))

# Function to generate upload middleware
def generate_upload_middleware():
    upload_code = '''
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const dir = './uploads/';
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir);
        }
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        cb(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname));
    }
});

const upload = multer({ storage: storage });

module.exports = upload;
'''
    with open('./middleware/upload.js', 'w') as file:
        file.write(upload_code)

# Main function to set up the project
def setup_project(file_path):
    # Read model data from Excel
    models = read_excel(file_path)

    # Create necessary directories
    os.makedirs('./models', exist_ok=True)
    os.makedirs('./controllers', exist_ok=True)
    os.makedirs('./uploads', exist_ok=True)  # Directory for file uploads
    os.makedirs('./middleware', exist_ok=True)  # Directory for middleware

    # Generate model files with relationships and proper data types
    generate_model_files(models)

    # Generate controller files with CRUD operations and download report
    generate_controller_files(models)

    # Generate upload middleware
    generate_upload_middleware()

    print('Project setup complete.')

# File path to the Excel sheet
excel_file_path = 'Testing Model Techhelps.xlsx'  # Replace with actual path

# Run the project setup
setup_project(excel_file_path)
