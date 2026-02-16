function handleAttendance(action) {
                fetch(`/my/attendance/${action}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: ''
                }).then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    }
                });
            }