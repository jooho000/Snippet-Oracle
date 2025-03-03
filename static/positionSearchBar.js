const navbar = $("#mobile-search");
const searchbar = $("#searchbar-Div");
const initPos = $("#init-pos");
const t1 = $("#title");
let past = false;
let resizing = false;

/**
 * Triggers searchbar move once scrolled past
 */
addEventListener("scroll", checkScrollHeight);

/**
 *
 * trigger search bar resizing on window size change
 */
addEventListener("resize", () => {
  if (past) resizeSearchbar();
});

/**
 * Resizes searchbar
 */
function resizeSearchbar() {
  searchInput.removeClass("is-large");
  if ($("#navbarBasic").css("display") == "flex")
    $("#desktop-search").append(searchbar);
  else $("#mobile-search").append(searchbar);
}

/**
 * Restores searchbar size and initial position
 */
function restoreDefaults() {
  searchInput.addClass("is-large");
  initPos.append(searchbar);
}

/**
 * checks scroll height triggesr changes if needed
 */
function checkScrollHeight() {
  if (!past && navbar.offset().top > initPos.offset().top) {
    past = true;
    resizeSearchbar();
  } else if (past && navbar.offset().top < initPos.offset().top) {
    past = false;
    restoreDefaults();
  }
}
