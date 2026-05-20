# Next frontend fix steps (will be applied now)

1. Update `accounts/templates/accounts/public_form_detail.html`
   - Make summary cards responsive via clean classes
   - Add unique accordion ids/prefixes for chart vs text
   - Add data attributes to scope accordion toggles

2. Update `accounts/static/accounts/css/public_from_detail.css`
   - Fix summary grid desktop 3-column / mobile stack
   - Ensure question cards look like cards with modern enterprise styling
   - Fix any CSS conflicts that affect accordion visuals

3. Update `accounts/static/accounts/js/public_form_detail.js`
   - Fix accordion behavior so chart questions close each other only
   - Fix text response accordions to open independently
   - Lazy-init Chart.js on first open
   - Reduce bar width and ensure chart.resize on open

