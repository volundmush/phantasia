const Phantasia = {

    handleLogin(event) {
        const xhr = event.detail.xhr;
        if (xhr.status === 401) {
            // Handle error
        } else if (xhr.status === 200) {
            window.location.href = "/dashboard";
        }
    },

  handleRegister(event) {
        const xhr = event.detail.xhr;
        if (xhr.status === 401) {
            // Handle error
        } else if (xhr.status === 200) {
            window.location.href = "/dashboard";
        }
    },
}

export default Phantasia;