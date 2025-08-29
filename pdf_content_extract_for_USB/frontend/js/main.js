/**
 * USB PD Specification Parser Frontend
 * Main JavaScript file for handling user interactions and API communication
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileName = document.getElementById('fileName');
    const parseBtn = document.getElementById('parseBtn');
    const progressSection = document.getElementById('progressSection');
    const progressStep = document.getElementById('progressStep');
    const progressPercentage = document.getElementById('progressPercentage');
    const progressFill = document.getElementById('progressFill');
    const progressLogs = document.getElementById('progressLogs');
    const resultsSection = document.getElementById('resultsSection');
    
    // Results elements
    const tocCount = document.getElementById('tocCount');
    const sectionsCount = document.getElementById('sectionsCount');
    const coveragePct = document.getElementById('coveragePct');
    
    // Modal elements
    const jsonModal = document.getElementById('jsonModal');
    const modalTitle = document.getElementById('modalTitle');
    const jsonViewer = document.getElementById('jsonViewer');
    const closeModal = document.getElementById('closeModal');
    const expandAll = document.getElementById('expandAll');
    const collapseAll = document.getElementById('collapseAll');
    const jsonSearch = document.getElementById('jsonSearch');
    
    // Action buttons
    const viewTocBtn = document.getElementById('viewTocBtn');
    const downloadTocBtn = document.getElementById('downloadTocBtn');
    const viewSectionsBtn = document.getElementById('viewSectionsBtn');
    const downloadSectionsBtn = document.getElementById('downloadSectionsBtn');
    const viewReportBtn = document.getElementById('viewReportBtn');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const viewMetadataBtn = document.getElementById('viewMetadataBtn');
    const downloadMetadataBtn = document.getElementById('downloadMetadataBtn');
    
    // Parsing options
    const extractToc = document.getElementById('extractToc');
    const extractSections = document.getElementById('extractSections');
    const generateReport = document.getElementById('generateReport');
    const enhanceContent = document.getElementById('enhanceContent');
    
    // Stored data
    let uploadedFile = null;
    let parsingResults = {
        jobId: null,
        toc: [],
        sections: [],
        metadata: {},
        validation: {}
    };
    
    // Event Listeners
    
    // File input change
    fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files);
    });
    
    // Drag and drop handlers
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('active');
    });
    
    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('active');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('active');
        handleFileSelect(e.dataTransfer.files);
    });
    
    // Parse button click
    parseBtn.addEventListener('click', function() {
        if (uploadedFile) {
            startParsing();
        }
    });
    
    // Modal close button
    closeModal.addEventListener('click', function() {
        jsonModal.style.display = 'none';
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(e) {
        if (e.target === jsonModal) {
            jsonModal.style.display = 'none';
        }
    });
    
    // Expand/collapse JSON viewer
    expandAll.addEventListener('click', function() {
        expandJsonViewer(true);
    });
    
    collapseAll.addEventListener('click', function() {
        expandJsonViewer(false);
    });
    
    // JSON search
    jsonSearch.addEventListener('input', function() {
        searchJsonViewer(this.value);
    });
    
    // Result action buttons
    viewTocBtn.addEventListener('click', function() {
        showJsonInModal('Table of Contents', parsingResults.toc);
    });
    
    downloadTocBtn.addEventListener('click', function() {
        downloadFile('usb_pd_toc.jsonl', 'toc');
    });
    
    viewSectionsBtn.addEventListener('click', function() {
        showJsonInModal('All Sections', parsingResults.sections);
    });
    
    downloadSectionsBtn.addEventListener('click', function() {
        downloadFile('usb_pd_spec.jsonl', 'spec');
    });
    
    viewReportBtn.addEventListener('click', function() {
        showJsonInModal('Validation Report', parsingResults.validation);
    });
    
    downloadReportBtn.addEventListener('click', function() {
        downloadFile('usb_pd_validation_report.xlsx', 'report');
    });
    
    // Metadata button handlers
    viewMetadataBtn.addEventListener('click', function() {
        showJsonInModal('Metadata', parsingResults.metadata);
    });
    
    downloadMetadataBtn.addEventListener('click', function() {
        downloadFile('usb_pd_metadata.jsonl', 'metadata');
    });
    
    // File handling functions
    
    function handleFileSelect(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Check if it's a PDF
            if (file.type !== 'application/pdf') {
                addLog('Error: Please upload a PDF file', 'error');
                return;
            }
            
            uploadedFile = file;
            fileName.textContent = file.name;
            parseBtn.disabled = false;
            
            addLog(`File selected: ${file.name} (${formatFileSize(file.size)})`, 'info');
        }
    }
    
    // Parsing functions
    
    function startParsing() {
        // Reset UI
        progressSection.style.display = 'block';
        resultsSection.style.display = 'none';
        progressLogs.innerHTML = '';
        setProgress(0, 'Preparing to process PDF...');
        
        // Create form data for upload
        const formData = new FormData();
        formData.append('file', uploadedFile);
        
        // Add options
        formData.append('extractToc', extractToc.checked);
        formData.append('extractSections', extractSections.checked);
        formData.append('generateReport', generateReport.checked);
        formData.append('enhanceContent', enhanceContent.checked);
        
        // Log start of upload
        addLog(`Uploading ${uploadedFile.name}...`);
        
        // Upload file and process it
        fetch('/api/parse', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Store job ID and file paths
            const jobId = data.job_id;
            const filePaths = data.file_paths;
            
            // Store results
            parsingResults.jobId = jobId;
            parsingResults.metadata = data.metadata;
            parsingResults.validation = data.coverage;
            
            // Log success
            addLog(`Processing complete. Job ID: ${jobId}`);
            setProgress(100, 'PDF processing complete');
            
            // Load TOC data
            addLog('Loading Table of Contents data...');
            
            // Load the TOC data - use parsingResults.jobId to ensure it's in scope
            return fetch(`/api/files/${parsingResults.jobId}/toc`);
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load TOC data');
            }
            return response.text();
        })
        .then(text => {
            // Parse JSONL content
            const lines = text.split('\n').filter(line => line.trim());
            parsingResults.toc = lines.map(line => JSON.parse(line));
            addLog(`Loaded ${parsingResults.toc.length} ToC sections`);
            
            // Load sections data
            addLog('Loading Sections data...');
            // Need to use parsingResults.jobId instead of jobId to ensure it's in scope
            return fetch(`/api/files/${parsingResults.jobId}/spec`);
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load Sections data');
            }
            return response.text();
        })
        .then(text => {
            // Parse JSONL content
            const lines = text.split('\n').filter(line => line.trim());
            parsingResults.sections = lines.map(line => JSON.parse(line));
            addLog(`Loaded ${parsingResults.sections.length} content sections`);
            
            // Load metadata if not already loaded from the API response
            if (!parsingResults.metadata || Object.keys(parsingResults.metadata).length === 0) {
                addLog('Loading metadata...');
                return fetch(`/api/files/${parsingResults.jobId}/metadata`);
            } else {
                // If metadata is already loaded, proceed to finalize
                addLog('Using metadata from API response');
                finalizeParsing();
                return null;
            }
        })
        .then(response => {
            if (!response) return; // Skip if metadata was already loaded
            
            if (!response.ok) {
                addLog('Warning: Failed to load metadata, using default', 'warning');
                return null;
            }
            return response.text();
        })
        .then(text => {
            if (!text) return; // Skip if metadata was already loaded or failed to load
            
            try {
                // Try to parse as JSON or JSONL
                if (text.trim().startsWith('{')) {
                    // Regular JSON
                    parsingResults.metadata = JSON.parse(text);
                } else {
                    // JSONL - take first non-empty line
                    const lines = text.split('\n').filter(line => line.trim());
                    if (lines.length > 0) {
                        parsingResults.metadata = JSON.parse(lines[0]);
                    }
                }
                addLog('Metadata loaded successfully');
            } catch (error) {
                addLog('Error parsing metadata: ' + error.message, 'error');
                console.error('Error parsing metadata:', error);
                // Create a default metadata object if parsing fails
                parsingResults.metadata = {
                    doc_title: uploadedFile ? uploadedFile.name.replace('.pdf', '') : 'USB Power Delivery Specification',
                    processing_date: new Date().toISOString()
                };
            }
            
            // Update results UI and show results
            finalizeParsing();
        })
        .catch(error => {
            addLog(`Error: ${error.message}`, 'error');
            console.error('Error processing PDF:', error);
        });
    }
    
    function simulateParsingProcess() {
        const stages = [
            { name: 'Initializing parser', duration: 500, progress: 5 },
            { name: 'Loading PDF file', duration: 1500, progress: 10 },
            { name: 'Analyzing document structure', duration: 2000, progress: 20 },
            { name: 'Extracting Table of Contents', duration: 3000, progress: 40 },
            { name: 'Parsing all sections', duration: 4000, progress: 70 },
            { name: 'Validating extracted content', duration: 2000, progress: 85 },
            { name: 'Generating report', duration: 1500, progress: 95 },
            { name: 'Completing process', duration: 500, progress: 100 }
        ];
        
        let currentStage = 0;
        
        function processStage() {
            if (currentStage < stages.length) {
                const stage = stages[currentStage];
                setProgress(stage.progress, stage.name);
                addLog(`${stage.name}...`);
                
                setTimeout(() => {
                    // Generate mock data based on the stage
                    generateMockData(stage.name);
                    
                    currentStage++;
                    processStage();
                }, stage.duration);
            } else {
                // Parsing complete
                finalizeParsing();
            }
        }
        
        processStage();
    }
    
    function generateMockData(stageName) {
        // Create mock data based on the current stage
        switch(stageName) {
            case 'Extracting Table of Contents':
                parsingResults.toc = generateMockToc();
                addLog(`Extracted ${parsingResults.toc.length} sections from Table of Contents`);
                break;
                
            case 'Parsing all sections':
                parsingResults.sections = generateMockSections(parsingResults.toc);
                addLog(`Extracted ${parsingResults.sections.length} sections from document`);
                break;
                
            case 'Validating extracted content':
                parsingResults.validation = generateMockValidation();
                addLog(`Validation complete: Coverage ${parsingResults.validation.coverage_percentage.toFixed(1)}%`);
                break;
                
            case 'Generating report':
                // Mock metadata
                parsingResults.metadata = {
                    doc_title: uploadedFile.name.replace('.pdf', ''),
                    total_toc_sections: parsingResults.toc.length,
                    total_sections: parsingResults.sections.length,
                    processing_date: new Date().toISOString(),
                    source_file: uploadedFile.name
                };
                
                addLog(`Report generated successfully`);
                break;
        }
    }
    
    function finalizeParsing() {
        // Update results UI
        tocCount.textContent = parsingResults.toc.length;
        sectionsCount.textContent = parsingResults.sections.length;
        coveragePct.textContent = `${parsingResults.validation.coverage_percentage.toFixed(1)}%`;
        
        // Show results section
        resultsSection.style.display = 'block';
        
        addLog('Parsing completed successfully!', 'success');
    }
    
    // UI helper functions
    
    function setProgress(percent, message) {
        progressStep.textContent = message;
        progressPercentage.textContent = `${percent}%`;
        progressFill.style.width = `${percent}%`;
    }
    
    function addLog(message, type = 'info') {
        const logEntry = document.createElement('p');
        logEntry.className = `log-entry log-${type}`;
        logEntry.textContent = message;
        progressLogs.appendChild(logEntry);
        progressLogs.scrollTop = progressLogs.scrollHeight;
    }
    
    function showJsonInModal(title, data) {
        modalTitle.textContent = title;
        renderJsonViewer(data);
        jsonModal.style.display = 'block';
    }
    
    function renderJsonViewer(data) {
        // Format JSON with syntax highlighting
        const formatted = JSON.stringify(data, null, 2);
        jsonViewer.innerHTML = `<pre class="json">${escapeHtml(formatted)}</pre>`;
        
        // In a real app, you'd use a proper JSON viewer library
        // This is a simplified version
        highlightJson(jsonViewer.querySelector('pre'));
    }
    
    function highlightJson(element) {
        // Simple JSON syntax highlighting
        let html = element.innerHTML;
        
        // Highlight keys
        html = html.replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>');
        
        // Highlight strings
        html = html.replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>');
        
        // Highlight numbers
        html = html.replace(/: (\d+)/g, ': <span class="json-number">$1</span>');
        
        // Highlight booleans and null
        html = html.replace(/: (true|false|null)/g, ': <span class="json-boolean">$1</span>');
        
        element.innerHTML = html;
    }
    
    function expandJsonViewer(expand) {
        // In a real implementation, this would expand/collapse JSON nodes
        // For this demo, it's just a placeholder
        addLog(`${expand ? 'Expanded' : 'Collapsed'} all JSON nodes`);
    }
    
    function searchJsonViewer(query) {
        // In a real implementation, this would search through the JSON
        // For this demo, it's just a placeholder
        if (query) {
            addLog(`Searching for: ${query}`);
        }
    }
    
    // Utility functions
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    function downloadFile(filename, fileType) {
        try {
            // Get the current job ID from the parsingResults
            const jobId = parsingResults.jobId;
            
            if (!jobId) {
                addLog('Warning: No job ID available. Trying to access root files...', 'warning');
                
                // If no job ID is available, try to get the file from the root path
                const rootUrl = `/${filename}`;
                addLog(`Accessing file at: ${rootUrl}`, 'info');
                window.open(rootUrl, '_blank');
                return;
            }
            
            // Download the file from the server API
            const apiUrl = `/api/files/${parsingResults.jobId}/${fileType}`;
            addLog(`Downloading file from: ${apiUrl}`, 'info');
            window.open(apiUrl, '_blank');
        } catch (error) {
            addLog(`Error downloading file: ${error.message}`, 'error');
            console.error('Error downloading file:', error);
        }
    }
    
    function downloadJson(filename, data) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Mock data generators
    
    function generateMockToc() {
        // Generate mock Table of Contents data
        const mockToc = [];
        const mainSections = 8; // Number of main sections
        
        for (let i = 1; i <= mainSections; i++) {
            // Add main section
            mockToc.push(createMockSection(
                `${i}`, 
                `Section ${i} Title`, 
                i + 5, // Mock page number
                1, 
                null
            ));
            
            // Add subsections
            const subsections = Math.floor(Math.random() * 5) + 1;
            for (let j = 1; j <= subsections; j++) {
                const sectionId = `${i}.${j}`;
                mockToc.push(createMockSection(
                    sectionId,
                    `Subsection ${sectionId} Title`,
                    i + 5 + j,
                    2,
                    `${i}`
                ));
                
                // Add some sub-subsections
                if (Math.random() > 0.5) {
                    const subSubsections = Math.floor(Math.random() * 3) + 1;
                    for (let k = 1; k <= subSubsections; k++) {
                        const subSectionId = `${i}.${j}.${k}`;
                        mockToc.push(createMockSection(
                            subSectionId,
                            `Sub-subsection ${subSectionId} Title`,
                            i + 5 + j + k,
                            3,
                            `${i}.${j}`
                        ));
                    }
                }
            }
        }
        
        return mockToc;
    }
    
    function generateMockSections(tocSections) {
        // Generate mock sections based on ToC
        const allSections = [...tocSections]; // Start with ToC sections
        
        // Add some additional sections not in ToC
        const additionalSections = Math.floor(tocSections.length * 0.2); // 20% more
        
        for (let i = 0; i < additionalSections; i++) {
            const randomSection = tocSections[Math.floor(Math.random() * tocSections.length)];
            const sectionId = `${randomSection.section_id}.${i + 1}`;
            
            allSections.push(createMockSection(
                sectionId,
                `Additional Section ${sectionId}`,
                randomSection.page + Math.floor(Math.random() * 5),
                randomSection.level + 1,
                randomSection.section_id
            ));
        }
        
        return allSections;
    }
    
    function generateMockValidation() {
        // Generate mock validation results
        const tocSections = parsingResults.toc.length;
        const allSections = parsingResults.sections.length;
        const commonSections = tocSections * 0.9; // 90% overlap
        
        return {
            total_toc: tocSections,
            total_spec: allSections,
            common: Math.floor(commonSections),
            toc_only: Math.floor(tocSections - commonSections),
            spec_only: Math.floor(allSections - commonSections),
            coverage_percentage: (commonSections / tocSections * 100),
            orphaned_sections: [],
            level_inconsistencies: [],
            parent_child_mismatches: []
        };
    }
    
    function createMockSection(id, title, page, level, parentId) {
        // Helper to create a mock section object
        return {
            section_id: id,
            title: title,
            page: page,
            level: level,
            parent_id: parentId,
            full_path: `${id} ${title}`,
            doc_title: "USB Power Delivery Specification"
        };
    }
    
    // Add initial log entry
    addLog('PDF Parser initialized. Please select a USB PD specification PDF file to begin.');
});
