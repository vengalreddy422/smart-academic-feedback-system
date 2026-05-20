# TODO - Public Form Analytics UI fixes

- [x] Update `accounts/templates/accounts/public_form_detail.html`

  - [ ] Ensure unique accordion body ids for chart vs text
  - [ ] Add wrapper classes/data attributes to scope toggling
  - [ ] Ensure visualization is hidden until open (proper initial markup)

- [ ] Update `accounts/static/accounts/css/public_from_detail.css`
  - [ ] Fix summary cards to render side-by-side on desktop, stacked on mobile/tablet
  - [ ] Ensure accordion cards/typography styling is consistent and enterprise-like
  - [ ] Improve chart responsiveness (heights) and spacing

- [ ] Update `accounts/static/accounts/js/public_form_detail.js`
  - [ ] Fix accordion open/close behavior: chart questions independent from text accordions
  - [ ] Fix multiple sections open bug due to conflicting selectors/ids
  - [ ] Implement lazy Chart.js rendering on accordion open
  - [ ] Reduce bar width professionally and call chart.resize() on open


- [ ] Manual verification
  - [ ] Desktop: summary cards 3 across
  - [ ] Mobile/tablet: summary cards stack
  - [ ] Only one chart accordion opens at a time
  - [ ] Clicking a text response accordion opens only itself
  - [ ] Charts only render after opening their card

