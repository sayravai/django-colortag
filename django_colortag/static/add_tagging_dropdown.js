const get_create_tagging_dropdown_closure = (function ($) {
  /** Get the dropdown creation function
    * @param {String} options.api_url - The url to the course instance in the A+ API,
    *        e.g. 'https://plus.cs.hut.fi/api/v2/courses/1'.
    * @param {String} options.api_taggings_url - suffix for taggings, default /taggings/
    * @param {String} options.api_tags_url - suffix for tags, default /usertags/
    * TODO: replace 'options' with object destructuring when supported by browsers.
    */
  return function get_create_tagging_dropdown_closure(options) {
    const default_settings = {
      api_taggings_url: 'taggings/',
      api_tags_url: 'usertags/',
    }
    // TODO: replace with spread syntax (ES2018) when supported by browsers
    const settings = $.extend({}, default_settings, options);
    if (typeof settings.api_url !== 'string') {
      throw new Error('Expected api_url');
    }
    if (settings.api_url.slice(-1) !== '/') {
      settings.api_url += '/';
    }

    /**
     * Send an AJAX post request to create a new tagging
     */
    function add_tagging(user_id, tag_slug) {
      const url = settings.api_url + settings.api_taggings_url;
      const request_body = JSON.stringify({
        user: { id: user_id },
        tag: { slug: tag_slug },
      });
      return $.ajax({
        type: 'POST',
        url: url,
        data: request_body,
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
      });
    }

    /**
     * Tag several users at once
     */
    function add_taggings(user_ids, tag_slug) {
      return user_ids.map(function (user_id) {
        return add_tagging(user_id, tag_slug);
      });
    }

    /**
     * Return f iff it is defined, and a do-nothing function otherwise
     */
    function f_or_empty(f) {
      return (typeof f !== 'undefined') ? f : function (x) {return;};
    }

    // Cache jqXHR containing the list of all usertags
    let xhr = undefined;
    const url = settings.api_url + settings.api_tags_url;
    function tags_xhr() {
      return xhr = xhr || $.ajax({
        type: 'GET',
        url: url,
        dataType: 'json',
      });
    }

    /**
     * Create a dropdown menu for adding new taggings
     *
     * @param {List<Int>} exclude_tag_ids - Tags to exclude from the dropdown.
     * @param {Function():List<Int>} get_users - A function that, when called,
     *        returns the list of user ids that should be tagged.
     * @param {String} button_text - The user-visible label of the dropdown.
     * @param {Function($elem:jQuery)} menu_created_callback - A callback that
     *        will be called with the dropdown once it has been created.
     * @param {Function(response:jqXHR)} click_callback - A callback that will
     *        be called with the AJAX response once the tag has been added.
     */
    return function (
      exclude_tag_ids,
      get_users,
      button_text,
      button_id,
      menu_created_callback,
      click_callback
    ) {
      menu_created_callback = f_or_empty(menu_created_callback);
      click_callback = f_or_empty(click_callback);

      const slug_id_prefix = 'tag-';

      const click_handler_for_slug = function (tag_slug) {
        return function (event) {
          const user_ids = get_users();
          click_callback(add_taggings(user_ids, tag_slug), tags_xhr());
          const tag_elem_id = slug_id_prefix + tag_slug;
          $('button#' + button_id + ' + ul > li#' + tag_elem_id).remove();
          return false;
        }
      }

      // Get the list of all tags and filter out excluded ones
      tags_xhr().done(function (data) {
        const all_tags = data.results;
        const tags = all_tags.filter(function (tag) {
          // true if tag.id is not null and it is not in exclude_tag_ids.
          // TODO: replace with Array.includes once IE is no longer relevant
          return tag.id !== null && exclude_tag_ids.indexOf(tag.id) === -1;
        });

        // Construct the dropdown
        // Use a div as the dropdown container (Bootstrap examples use div)
        const $span = $('<div />').addClass('dropdown create-tagging');
        const $button = $('<button />')
          .addClass('btn btn-secondary dropdown-toggle')
          .attr({
            'type': 'button',
            'id': button_id,
            // Support both Bootstrap 5 (data-bs-*) and older jQuery plugin (data-toggle)
            'data-bs-toggle': 'dropdown',
            'data-toggle': 'dropdown',
            'aria-haspopup': 'true',
            'aria-expanded': 'false',
          })
          .text(button_text);
        const $ul = $('<ul />')
          .addClass('dropdown-menu')
          .attr({ 'aria-labelledby': button_id });
        const $li_list = tags.map(function (tag) {
          const $li = $('<li />').attr({ 'id': slug_id_prefix + tag.slug });
          const $a = $('<a />')
            .attr({ href: '#' })
            .addClass('dropdown-item')
            .append(django_colortag_label(tag))
            .on('click', click_handler_for_slug(tag.slug));
          $li.append($a);
          return $li;
        });

        $ul.append($li_list);
        $span.append($button);
        $span.append($ul);
        // If Bootstrap 5 is available, initialize dropdown programmatically
        if (window.bootstrap && window.bootstrap.Dropdown) {
          try { new window.bootstrap.Dropdown($button[0]); } catch (e) { /* noop */ }
        }
        // Fallback: if no Bootstrap dropdown (neither BS5 nor BS3), toggle via simple class
        if (!(window.bootstrap && window.bootstrap.Dropdown) && !(typeof $.fn.dropdown === 'function')) {
          $button.on('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            const $toggle = $(this);
            const $menu = $toggle.next('.dropdown-menu');
            const willShow = !$menu.hasClass('show');
            // close any other open menus
            $('.dropdown .dropdown-menu.show').removeClass('show');
            $('.dropdown .dropdown-toggle[aria-expanded="true"]').attr('aria-expanded', 'false');
            if (willShow) {
              $menu.addClass('show');
              $toggle.attr('aria-expanded', 'true');
            }
          });
          // Close on outside click
          $(document).on('click.usertagdropdown', function () {
            $('.dropdown .dropdown-menu.show').removeClass('show');
            $('.dropdown .dropdown-toggle[aria-expanded="true"]').attr('aria-expanded', 'false');
          });
        }
        menu_created_callback($span);
      });
    }
  }
})(jQuery);
