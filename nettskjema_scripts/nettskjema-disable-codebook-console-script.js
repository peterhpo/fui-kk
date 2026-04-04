// Script for disabling Codebook on all relevant forms

const yearRegex = /\b(H|V)\d{4}\b/; // Regular expression to match titles

let csrfToken;       // Variable to hold the CSRF token
let errorForms = []; // Array to track forms that encounter errors

// Fetch CSRF token
const fetchCsrfToken = () => {
    return fetch("https://nettskjema.no/csrf", {
        method: "GET",
        credentials: "include"
    }).then(response => {
        if (!response.ok) throw new Error("Error fetching CSRF token");
        return response.text();
    });
};

// Fetch settings for a specific form
const fetchFormSettings = (formId) => {
    const url = `https://nettskjema.no/api/v3/form/${formId}/settings`;
    return fetch(url, {
        method: "GET",
        credentials: "include"
    }).then(response => {
        if (!response.ok) throw new Error(`Error fetching settings for form ID: ${formId}`);
        return response.json();
    });
};

// Disable Codebook for a specific form
const disableCodebook = (formId) => {
    const patchUrl = `https://nettskjema.no/api/v3/form/${formId}/settings`;
    const jsonData = { codebookActivated: false };

    console.log("Disabling Codebook for form ID:", formId);

    return fetch(patchUrl, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken
        },
        body: JSON.stringify(jsonData),
        credentials: "include"
    })
    .then(patchResponse => {
        if (patchResponse.ok) {
            console.log(`Successfully disabled Codebook for form ID: ${formId}`);
        } else {
            console.error(`Error disabling Codebook for form ID: ${formId}`, patchResponse);
            return patchResponse.text().then(text => {
                throw new Error(`Update failed: ${text}`);
            });
        }
    })
    .catch(error => {
        console.error("Error disabling Codebook for form ID:", formId, error);
        errorForms.push(formId);
    });
};

// Process forms in batches
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
                    if (formSettings.codebookActivated === false) {
                        console.log(`Skipping form ID ${form.formId}: Codebook already disabled.`);
                        return;
                    }
                    return disableCodebook(form.formId);
                });
            });

            return Promise.all(batchPromises).then(() => {
                // small pause between batches
                return new Promise(resolve => setTimeout(resolve, 200));
            });
        });
    }, Promise.resolve());
};

// Main execution
fetchCsrfToken()
    .then(token => {
        csrfToken = token;
        return fetch("https://nettskjema.no/api/v3/form/me", {
            method: "GET",
            credentials: "include"
        });
    })
    .then(response => {
        if (!response.ok) throw new Error("Error fetching forms");
        return response.json();
    })
    .then(forms => {
        const formsToUpdate = forms.filter(form => yearRegex.test(form.title));
        console.log("Forms to update (disable Codebook):", formsToUpdate);
        return processFormsInBatches(formsToUpdate).then(() => {
            console.log("Forms that failed when disabling Codebook:", errorForms);
        });
    })
    .catch(error => {
        console.error("Error:", error);
    });
