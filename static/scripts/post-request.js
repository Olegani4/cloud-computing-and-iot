async function sendPOST(endpoint, data = {}) {
    response = await fetch(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ data }),
    });

    return response;
}