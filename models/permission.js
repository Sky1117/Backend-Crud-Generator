const mongoose = require('mongoose');
const PermissionSchema = new mongoose.Schema({
    name: { type: String },
    created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    is_active: { type: Boolean, default: true },
}, { timestamps: true });
module.exports = mongoose.model('Permission', PermissionSchema);
