document.addEventListener('DOMContentLoaded', () => {
    send_query();
});

function send_query() {

    console.log("send query...")

    document.getElementById('results').innerHTML = '';
    document.getElementById("results_not_found").style.display = "none";
    console.log("hide not found icon");

    const filters = document.querySelectorAll('#filters input:not(#authors_filter):not(#tags_filter):not([id^="pub_type_"]):not(#date_from):not(#date_to):not(#anyDate), #filters select:not(#publication_types_advanced), #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            const csrfToken = document.getElementById('csrf_token').value;

            const searchCriteria = {
                csrf_token: csrfToken,
                query: document.querySelector('#query').value,
                publication_type: document.querySelector('#publication_type').value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log(document.querySelector('#publication_type').value);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchCriteria),
            })
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    // results counter
                    const resultCount = data.length;
                    const resultText = resultCount === 1 ? 'dataset' : 'datasets';
                    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

                    if (resultCount === 0) {
                        console.log("show not found icon");
                        document.getElementById("results_not_found").style.display = "block";
                    } else {
                        document.getElementById("results_not_found").style.display = "none";
                    }


                    data.forEach(dataset => {
                        let card = document.createElement('div');
                        card.className = 'col-12';
                        card.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center justify-content-between">
                                        <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                                        <div>
                                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                                        </div>
                                    </div>
                                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Description
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <p class="card-text">${dataset.description}</p>
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Authors
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.authors.map(author => `
                                                <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                            `).join('')}
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Tags
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                        </div>

                                    </div>

                                    <div class="row">

                                        <div class="col-md-4 col-12">

                                        </div>
                                        <div class="col-md-8 col-12">
                                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                View dataset
                                            </a>
                                            <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                Download (${dataset.total_size_in_human_format})
                                            </a>
                                        </div>


                                    </div>

                                </div>
                            </div>
                        `;

                        document.getElementById('results').appendChild(card);
                    });
                });
        });
    });
}

function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('query');
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            // Set the value of the select to the value of the matching option
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {

    // Reset the search query
    let queryInput = document.querySelector('#query');
    queryInput.value = "";
    // queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    // Reset the publication type to its default value
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "any"; // replace "any" with whatever your default value is
    // publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));

    // Reset the sorting option
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest"; // replace "default" with whatever your default value is
        // option.dispatchEvent(new Event('input', {bubbles: true}));
    });

    // Perform a new search with the reset filters
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

document.addEventListener('DOMContentLoaded', () => {

    //let queryInput = document.querySelector('#query');
    //queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    let urlParams = new URLSearchParams(window.location.search);
    let queryParam = urlParams.get('query');

    if (queryParam && queryParam.trim() !== '') {

        const queryInput = document.getElementById('query');
        queryInput.value = queryParam
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event");

    } else {
        const queryInput = document.getElementById('query');
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
    }

    // Initialize advanced search functionality
    initializeAdvancedSearch();
});

// ==================== ADVANCED SEARCH FUNCTIONALITY ====================

let availableTags = []; // Will be populated from API
let availableAuthors = []; // Will be populated from API

function initializeAdvancedSearch() {

    // Toggle advanced filters panel
    const toggleButton = document.getElementById('toggleAdvancedSearch');
    const advancedPanel = document.getElementById('advancedFiltersPanel');
    const applyButton = document.getElementById('apply-advanced-filters');

    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            if (advancedPanel.style.display === 'none') {
                advancedPanel.style.display = 'block';
                applyButton.style.display = 'inline-block';
                toggleButton.innerHTML = '<i data-feather="filter"></i> Hide Advanced Filters';
                // Re-initialize feather icons
                if (window.feather) feather.replace();
            } else {
                advancedPanel.style.display = 'none';
                applyButton.style.display = 'none';
                toggleButton.innerHTML = '<i data-feather="filter"></i> Advanced Filters';
                // Re-initialize feather icons
                if (window.feather) feather.replace();
            }
        });
    }

    // Load available tags (disabled temporarily)
    // loadAvailableTags();

    // Setup author suggestions
    setupAuthorSuggestions();

    // Setup tag suggestions
    setupTagSuggestions();

    // Setup date filters
    setupDateFilters();

    // Setup advanced search button
    setupAdvancedSearchButton();
}

function loadAvailableTags() {
    fetch('/api/tags')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            availableTags = data;
        })
        .catch(error => {
            console.error('Error loading tags:', error);
            availableTags = []; // Fallback to empty array
        });
}

function setupAuthorSuggestions() {
    const authorsInput = document.getElementById('authors_filter');
    const suggestionsDiv = document.getElementById('authorSuggestions');

    if (authorsInput && suggestionsDiv) {
        console.log('Author suggestions setup enabled');
        
        let debounceTimer;

        authorsInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const term = this.value.split(',').pop().trim();
                if (term.length >= 2) {
                    fetchAuthorSuggestions(term);
                } else {
                    hideAuthorSuggestions();
                }
            }, 300);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!authorsInput.contains(event.target) && !suggestionsDiv.contains(event.target)) {
                hideAuthorSuggestions();
            }
        });
    }

    // Add Author button functionality
    const addAuthorBtn = document.getElementById('addAuthorBtn');
    if (addAuthorBtn) {
        addAuthorBtn.addEventListener('click', function() {
            const input = document.getElementById('authors_filter');
            if (input && input.value.trim()) {
                // Just focus back to input for more authors
                input.focus();
            }
        });
    }
}

function fetchAuthorSuggestions(term) {
    fetch(`/api/authors?term=${encodeURIComponent(term)}`)
        .then(response => {
            console.log('Author suggestions response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Response is not JSON');
            }
            return response.json();
        })
        .then(data => {
            console.log('Author suggestions data:', data);
            showAuthorSuggestions(data);
        })
        .catch(error => {
            console.error('Error fetching authors:', error);
            hideAuthorSuggestions();
        });
}

function showAuthorSuggestions(authors) {
    const suggestionsDiv = document.getElementById('authorSuggestions');
    
    if (!suggestionsDiv) return;
    
    suggestionsDiv.innerHTML = '';
    
    authors.forEach(author => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.href = '#';
        item.innerHTML = `
            <div>
                <strong>${author.name}</strong>
                ${author.orcid ? `<br><small class="text-muted">ORCID: ${author.orcid}</small>` : ''}
                ${author.affiliation ? `<br><small class="text-muted">${author.affiliation}</small>` : ''}
            </div>
        `;
        item.addEventListener('click', function(e) {
            e.preventDefault();
            addAuthorToInput(author.name);
            hideAuthorSuggestions();
        });
        suggestionsDiv.appendChild(item);
    });
    
    suggestionsDiv.style.display = authors.length > 0 ? 'block' : 'none';
}

function addAuthorToInput(authorName) {
    const input = document.getElementById('authors_filter');
    if (!input) return;
    
    const currentValue = input.value;
    const authors = currentValue.split(',').map(a => a.trim());
    authors[authors.length - 1] = authorName;
    input.value = authors.join(', ') + ', ';
    input.focus();
}

function hideAuthorSuggestions() {
    const suggestionsDiv = document.getElementById('authorSuggestions');
    if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
    }
}

function setupTagSuggestions() {
    const tagsInput = document.getElementById('tags_filter');
    const suggestionsDiv = document.getElementById('tagSuggestions');

    if (tagsInput && suggestionsDiv) {
        tagsInput.addEventListener('input', function() {
            const term = this.value.split(',').pop().trim();
            if (term.length > 0) {
                showTagSuggestions(term);
            } else {
                hideTagSuggestions();
            }
        });

        tagsInput.addEventListener('focus', function() {
            if (availableTags.length > 0) {
                showTagSuggestions('');
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!tagsInput.contains(event.target) && !suggestionsDiv.contains(event.target)) {
                hideTagSuggestions();
            }
        });
    }
}

function showTagSuggestions(term) {
    const suggestionsDiv = document.getElementById('tagSuggestions');
    
    if (!suggestionsDiv || availableTags.length === 0) return;
    
    const matchingTags = availableTags.filter(tag => 
        tag.toLowerCase().includes(term.toLowerCase())
    ).slice(0, 15); // Show max 15 suggestions
    
    suggestionsDiv.innerHTML = '';
    
    if (matchingTags.length === 0 && term === '') {
        // Show all tags when no filter
        availableTags.slice(0, 15).forEach(tag => {
            addTagSuggestion(suggestionsDiv, tag);
        });
    } else {
        matchingTags.forEach(tag => {
            addTagSuggestion(suggestionsDiv, tag);
        });
    }
    
    suggestionsDiv.style.display = suggestionsDiv.children.length > 0 ? 'block' : 'none';
}

function addTagSuggestion(container, tag) {
    const item = document.createElement('a');
    item.className = 'dropdown-item';
    item.href = '#';
    item.textContent = tag;
    item.addEventListener('click', function(e) {
        e.preventDefault();
        addTagToInput(tag);
        hideTagSuggestions();
    });
    container.appendChild(item);
}

function addTagToInput(tagName) {
    const input = document.getElementById('tags_filter');
    if (!input) return;
    
    const currentValue = input.value;
    const tags = currentValue.split(',').map(t => t.trim());
    
    // Check if tag already exists
    if (!tags.includes(tagName)) {
        tags[tags.length - 1] = tagName;
        input.value = tags.join(', ') + ', ';
    }
    input.focus();
}

function hideTagSuggestions() {
    const suggestionsDiv = document.getElementById('tagSuggestions');
    if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
    }
}

function setupDateFilters() {
    const anyDateCheckbox = document.getElementById('anyDate');
    const dateInputs = document.querySelectorAll('#date_from, #date_to');

    if (anyDateCheckbox) {
        anyDateCheckbox.addEventListener('change', function() {
            dateInputs.forEach(input => {
                input.disabled = this.checked;
                if (this.checked) input.value = '';
            });
        });
    }
}

function setupAdvancedSearchButton() {
    const applyButton = document.getElementById('apply-advanced-filters');
    
    if (applyButton) {
        applyButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            performAdvancedSearch();
        });
    }

    // Prevenir que los campos avanzados disparen la búsqueda básica
    const advancedFields = document.querySelectorAll('#authors_filter, #tags_filter, #date_from, #date_to, #anyDate, [id^="pub_type_"]');
    advancedFields.forEach(field => {
        field.addEventListener('input', function(e) {
            e.stopPropagation();
        });
        field.addEventListener('change', function(e) {
            e.stopPropagation();
        });
    });
}

function performAdvancedSearch() {
    
    const csrfToken = document.getElementById('csrf_token').value;
    
    // Collect all advanced search criteria
    const searchCriteria = {
        csrf_token: csrfToken,
        query: document.querySelector('#query')?.value || '',
        publication_type: document.querySelector('#publication_type')?.value || 'any',
        sorting: document.querySelector('[name="sorting"]:checked')?.value || 'newest',
        
        // Advanced filters
        authors_filter: document.getElementById('authors_filter')?.value || '',
        tags_filter: document.getElementById('tags_filter')?.value || '',
        publication_types_advanced: getSelectedPublicationTypes(),
        date_from: document.getElementById('date_from')?.value || '',
        date_to: document.getElementById('date_to')?.value || '',
        any_date: document.getElementById('anyDate')?.checked || false
    };

    // Clear existing results immediately
    document.getElementById('results').innerHTML = '';
    document.getElementById('results_number').textContent = 'Searching...';

    fetch('/explore', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchCriteria),
    })
    .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
        .then(data => {        // Clear existing results
        document.getElementById('results').innerHTML = '';
        document.getElementById("results_not_found").style.display = "none";
        
        // Update results counter
        const resultCount = data.length;
        const resultText = resultCount === 1 ? 'dataset' : 'datasets';
        document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

            if (resultCount === 0) {
                document.getElementById("results_not_found").style.display = "block";
            } else {
                document.getElementById("results_not_found").style.display = "none";            // Render results using existing function logic
            data.forEach(dataset => {
                let card = document.createElement('div');
                card.className = 'col-12';
                card.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex align-items-center justify-content-between">
                                <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                                <div>
                                    <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                                </div>
                            </div>
                            <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                            <div class="row mb-2">
                                <div class="col-md-4 col-12">
                                    <span class="text-secondary">Description</span>
                                </div>
                                <div class="col-md-8 col-12">
                                    <p class="card-text">${dataset.description}</p>
                                </div>
                            </div>

                            <div class="row mb-2">
                                <div class="col-md-4 col-12">
                                    <span class="text-secondary">Authors</span>
                                </div>
                                <div class="col-md-8 col-12">
                                    ${dataset.authors.map(author => `
                                        <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                    `).join('')}
                                </div>
                            </div>

                            <div class="row mb-2">
                                <div class="col-md-4 col-12">
                                    <span class="text-secondary">Tags</span>
                                </div>
                                <div class="col-md-8 col-12">
                                    ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-md-4 col-12"></div>
                                <div class="col-md-8 col-12">
                                    <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" style="border-radius: 5px;">
                                        View dataset
                                    </a>
                                    <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" style="border-radius: 5px;">
                                        Download (${dataset.total_size_in_human_format})
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('results').appendChild(card);
            });
        }
    })
    .catch(error => {
        console.error('Error performing advanced search:', error);
        document.getElementById('results_number').textContent = 'Error occurred';
        document.getElementById('results').innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${error.message}
                </div>
            </div>
        `;
    });
}

function getSelectedPublicationTypes() {
    const checkboxes = document.querySelectorAll('#advancedFiltersPanel input[type="checkbox"][id^="pub_type_"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Extend the existing clearFilters function to include advanced filters
const originalClearFilters = clearFilters;
clearFilters = function() {
    // Call original clear filters
    originalClearFilters();
    
    // Clear advanced filters
    clearAdvancedFilters();
}

function clearAdvancedFilters() {
    // Clear author filter
    const authorsInput = document.getElementById('authors_filter');
        if (authorsInput) {
            authorsInput.value = '';
            hideAuthorSuggestions();
        }    // Clear tags filter
    const tagsInput = document.getElementById('tags_filter');
    if (tagsInput) tagsInput.value = '';
    
    // Clear publication type checkboxes
    const pubTypeCheckboxes = document.querySelectorAll('#advancedFiltersPanel input[type="checkbox"]');
    pubTypeCheckboxes.forEach(cb => cb.checked = false);
    
    // Clear date filters
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');
    const anyDate = document.getElementById('anyDate');
    
    if (dateFrom) dateFrom.value = '';
    if (dateTo) dateTo.value = '';
    if (anyDate) {
        anyDate.checked = false;
        // Re-enable date inputs
        if (dateFrom) dateFrom.disabled = false;
        if (dateTo) dateTo.disabled = false;
    }
    
    // Hide advanced panel
    const advancedPanel = document.getElementById('advancedFiltersPanel');
    const applyButton = document.getElementById('apply-advanced-filters');
    const toggleButton = document.getElementById('toggleAdvancedSearch');
    
    if (advancedPanel) advancedPanel.style.display = 'none';
    if (applyButton) applyButton.style.display = 'none';
    if (toggleButton) {
        toggleButton.innerHTML = '<i data-feather="filter"></i> Advanced Filters';
        // Re-initialize feather icons
        if (window.feather) feather.replace();
    }
    
    console.log("Advanced filters cleared");
}