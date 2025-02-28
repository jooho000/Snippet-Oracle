const navbar = $("#mobile-search");
const searchbar = $("#searchbar-Div");
const initPos = $("#init-pos");
const t1 = $("#title");
let past = false;
let resizing = false;

/**
 * Triggers searchbar move once scrolled past
 */
addEventListener("scroll", () => {
  checkScrollHeight();
});

/**
 *
 * trigger search bar resizing on window size change
 */
addEventListener("resize", () => {
  if (past){
    resizeSearchbar();
  }
});

/**
 * Resizes searchbar
 */
function resizeSearchbar() {
  searchInput.removeClass("is-large");
  if ($("#navbarBasic").css("display") == "flex") {
    $("#desktop-search").append(searchbar);
    searchbar.removeClass("mt-2").addClass("mt-3");
  } else {
    $("#mobile-search").append(searchbar);
    searchbar.removeClass("mt-3").addClass("mt-2");
  }
}

/**
 * Restores searchbar size and initial position
 */
function restoreDefaults() {
  searchInput.addClass("is-large");
  searchbar.removeClass("mt-3").removeClass("mt-2");
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