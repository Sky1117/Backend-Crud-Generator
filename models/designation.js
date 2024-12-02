const mongoose = require('mongoose');
const DesignationSchema = new mongoose.Schema({
    name: { type: String },
    reportTo: { type: String },
    permission: { type: mongoose.Schema.Types.ObjectId, ref: 'Permission' },
    created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    is_active: { type: Boolean, default: true },
}, { timestamps: true });
module.exports = mongoose.model('Designation', DesignationSchema);
