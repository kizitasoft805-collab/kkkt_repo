<script>
    // Toggle Sidebar
    const sidebarToggle = document.getElementById('sidebarToggle');
    sidebarToggle.addEventListener('click', function () {
        const sidebar = document.getElementById('sidebar'); // Adjust ID to match your sidebar
        sidebar.classList.toggle('hidden');
    });

    // Logout Functionality
    const logoutIcon = document.getElementById('logoutIcon');
    logoutIcon.addEventListener('click', function () {
        if (confirm('Are you sure you want to log out?')) {
            window.location.href = '/logout/'; // Adjust logout URL as needed
        }
    });

    // Search Sidebar Links
    const sidebarSearch = document.getElementById('sidebarSearch');
    sidebarSearch.addEventListener('input', function (event) {
        const query = event.target.value.toLowerCase();
        const sidebarLinks = document.querySelectorAll('#sidebar a'); // Adjust selector to match your sidebar links

        sidebarLinks.forEach(link => {
            if (link.textContent.toLowerCase().includes(query)) {
                link.style.display = ''; // Show matching link
            } else {
                link.style.display = 'none'; // Hide non-matching link
            }
        });
    });
</script>
