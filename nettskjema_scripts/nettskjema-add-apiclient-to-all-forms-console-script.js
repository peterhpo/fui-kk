// Script for adding the API-client to all relevant forms

const newEditorUsername = "a6bda462-18ee-4ad2-8661-f3bee122e91f@apiclient"; // Your API client username
const openToDate = "2026-06-17T20:35:34.376"; // Example date for the openTo
const yearRegex = /\b(H|V)\d{4}\b/; // Regular expression to match titles

let csrfToken; // Variable to hold the CSRF token
let errorForms = []; // Array to track forms that encounter errors

// Function to fetch CSRF token
const fetchCsrfToken = () => {
    return fetch("https://nettskjema.no/csrf", {
        method: 'GET',
        credentials: 'include' // Include cookies for authentication
    }).then(response => {
        if (!response.ok) throw new Error("Error fetching CSRF token");
        return response.text();
    });
};

// Function to fetch form settings for a specific form ID
const fetchFormSettings = (formId) => {
    const url = `https://nettskjema.no/api/v3/form/${formId}/settings`;
    return fetch(url, {
        method: 'GET',
        credentials: 'include'
    }).then(response => {
        if (!response.ok) throw new Error(`Error fetching settings for form ID: ${formId}`);
        return response.json();
    });
};

// Function to update editors and settings for the specific form
const updateFormSettings = (formId, editors) => {
    const patchUrl = `https://nettskjema.no/api/v3/form/${formId}/settings`;

    const jsonData = {
        "editors": editors.concat({
            "username": newEditorUsername
        }),
        "netgroupsEditor": [
            {
                "netgroupId": 1224,
                "name": "fui"
            }
        ],
        "globalCopyPermissionEnabled": false
    };

    console.log('Updating settings for form ID:', formId);

    return fetch(patchUrl, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken // Use the already fetched CSRF token
        },
        body: JSON.stringify(jsonData),
        credentials: 'include' // Include cookies for session management
    }).then(patchResponse => {
        if (patchResponse.ok) {
            console.log(`Successfully updated form ID: ${formId}`);
        } else {
            console.error(`Error updating form ID: ${formId}`, patchResponse);
            return patchResponse.text().then(text => {
                throw new Error(`Update failed: ${text}`);
            });
        }
    }).catch(error => {
        // Track the form ID with issues
        console.error('Error updating form ID:', formId, error);
        errorForms.push(formId); // Store the form ID that failed
    });
};

// Function to open a form
const openForm = (formId) => {
    const openUrl = `https://nettskjema.no/api/v3/private/form/${formId}/open`;
    return fetch(openUrl, {
        method: 'PATCH',
        credentials: 'include'
    }).then(response => {
        if (response.ok) {
            console.log(`Successfully opened form ID: ${formId}`);
        } else if (response.status === 403) {
            console.warn(`Skipping form ID ${formId}: permission denied.`);
        } else {
            throw new Error(`Error opening form ID: ${formId}`);
        }
    });
};

// Function to set openTo date
const setOpenToDate = (formId) => {
    const settingsUrl = `https://nettskjema.no/api/v3/form/${formId}/settings`;
    return fetch(settingsUrl, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken // Use the CSRF token
        },
        body: JSON.stringify({ "openTo": openToDate }),
        credentials: 'include'
    }).then(response => {
        if (!response.ok) throw new Error(`Error setting openTo for form ID: ${formId}`);
        console.log(`Successfully set openTo date for form ID: ${formId}`);
    });
};

// Function to close a form
const closeForm = (formId) => {
    const closeUrl = `https://nettskjema.no/api/v3/private/form/${formId}/close`;
    return fetch(closeUrl, {
        method: 'PATCH',
        headers: { 'X-CSRF-Token': csrfToken }, // Include token
        credentials: 'include' // Include cookies for session management
    }).then(response => {
        if (!response.ok) throw new Error(`Error closing form ID: ${formId}`);
        console.log(`Successfully closed form ID: ${formId}`);
    });
};

// Function to process forms in batches
const processFormsInBatches = (forms) => {
    const batchSize = 10; // Number of forms to process concurrently
    const batches = [];

    for (let i = 0; i < forms.length; i += batchSize) {
        batches.push(forms.slice(i, i + batchSize));
    }

    return batches.reduce((promise, batch) => {
        return promise.then(() => {
            const batchPromises = batch.map(form => {
                return fetchFormSettings(form.formId).then(formSettings => {
                    const existingEditors = formSettings.editors;

                    // Check if the newEditorUsername already exists
                    const editorExists = existingEditors.some(editor => editor.username === newEditorUsername);
                    
                    if (editorExists) {
                        console.log(`Skipping update for form ID ${form.formId} because ${newEditorUsername} already has access.`);
                        return; // Skip this form
                    }

                    // Update the settings
                    return updateFormSettings(form.formId, existingEditors);
                });
            });

            return Promise.all(batchPromises).then(() => {
                return new Promise(resolve => setTimeout(resolve, 200)); // Delay between batches
            });
        });
    }, Promise.resolve()); // Start with a resolved promise
};

// Main execution
fetchCsrfToken()
    .then(token => {
        csrfToken = token; // Store CSRF token
        return fetch("https://nettskjema.no/api/v3/form/me", {
            method: 'GET',
            credentials: 'include'
        });
    })
    .then(response => {
        if (!response.ok) throw new Error("Error fetching forms");
        return response.json();
    })
    .then(forms => {
        const formsToUpdate = forms.filter(form => yearRegex.test(form.title));
        console.log('Forms to Update:', formsToUpdate);
        return processFormsInBatches(formsToUpdate).then(() => {
            // At the end, log the forms with errors
            console.log('Forms that need error handling:', errorForms);
            // Process error forms after handling updates
            handleErrors(errorForms);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });

// Function to handle errors for forms that need reopening, setting, and closing
const handleErrors = (formsWithErrors) => {
    if (formsWithErrors.length > 0) {
        // Process each form in a single-threaded manner
        const handleFormErrors = async () => {
            for (const formId of formsWithErrors) {
                try {
                    await openForm(formId);
                    await setOpenToDate(formId);
                    await closeForm(formId);
                    console.log(`Handled form ID: ${formId}`);
                } catch (err) {
                    console.error(`Failed to handle form ID: ${formId}`, err);
                }
            }
        };

        handleFormErrors(); // Start processing
    } else {
        console.log('No forms to handle errors for.');
    }
};
