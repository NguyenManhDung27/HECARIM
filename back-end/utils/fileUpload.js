const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Configure multer for file storage
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadPath = path.join(__dirname, '../public/uploads');
        
        // Create directory if it doesn't exist
        if (!fs.existsSync(uploadPath)) {
            fs.mkdirSync(uploadPath, { recursive: true });
        }

        // Create subdirectory based on file type
        const fileType = getFileType(file.mimetype);
        const typePath = path.join(uploadPath, fileType);
        
        if (!fs.existsSync(typePath)) {
            fs.mkdirSync(typePath, { recursive: true });
        }

        cb(null, typePath);
    },
    filename: function (req, file, cb) {
        // Generate unique filename
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

// File filter
const fileFilter = (req, file, cb) => {
    // Accept images, PDFs, and common document formats
    const allowedMimes = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (allowedMimes.includes(file.mimetype)) {
        cb(null, true);
    } else {
        cb(new Error('Định dạng file không được hỗ trợ'), false);
    }
};

// Configure multer
const upload = multer({
    storage: storage,
    fileFilter: fileFilter,
    limits: {
        fileSize: 10 * 1024 * 1024, // 10MB limit
        files: 5 // Maximum 5 files per upload
    }
});

// Helper function to determine file type directory
function getFileType(mimetype) {
    if (mimetype.startsWith('image/')) return 'images';
    if (mimetype === 'application/pdf') return 'documents';
    if (mimetype.includes('word')) return 'documents';
    if (mimetype.includes('excel')) return 'spreadsheets';
    return 'others';
}

// Process uploaded files
function processUploadedFiles(files) {
    return files.map(file => ({
        filename: file.filename,
        originalName: file.originalname,
        path: file.path.replace(/\\/g, '/').split('public/')[1],
        type: file.mimetype,
        size: file.size,
        uploadedAt: new Date()
    }));
}

// Delete file
function deleteFile(filepath) {
    const fullPath = path.join(__dirname, '../public', filepath);
    if (fs.existsSync(fullPath)) {
        fs.unlinkSync(fullPath);
        return true;
    }
    return false;
}

module.exports = {
    upload,
    processUploadedFiles,
    deleteFile
};