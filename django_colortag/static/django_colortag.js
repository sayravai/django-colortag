function django_colortag_label(colortag, options_) {
  // Almost a direct port of templatetags/colortag.py:render_as_button
  const default_options = {
    active: true,
    static: true,
    element: 'span',
    label: true,
  }
  const options = jQuery.extend({}, default_options, options_);

  const attrs = {
    'data-tagid': colortag.id,
    'data-tagslug': colortag.slug,
    'data-background': colortag.color,
  };
  if (!options['no_tooltip'] && colortag.description) {
    $.extend(attrs, {
      'data-bs-toggle': 'tooltip',
      'data-bs-trigger': options['tooltip_trigger'] || 'hover',
      'data-bs-placement': options['tooltip_placement'] || 'top',
      'title': colortag.description,
    });
  }

  const classes = ['colortag'];
  classes.push(colortag.font_white ? 'colortag-dark' : 'colortag-light');
  if (options['active']) {
    classes.push('colortag-active');
  }
  if (options['button']) {
    classes.push('btn');
  }
  if (options['label']) {
    classes.push('label', 'label-' + (options['size'] || 'xs'));
  }
  if (options['class']) {
    classes.push(options['class'].split(' '));
  }
  attrs['class'] = classes.join(' ');
  attrs['style'] = '--colortag-color: ' + colortag.color + ';';

  for (var k in colortag['data-attrs']) {
    attrs['data-tag' + k] = colortag['data-attrs'][k];
  }

  const attr_strings = Object.keys(attrs).map(function (k) {
    return k + '="' + attrs[k] + '"';
  });
  const flatatt = attr_strings.join(' ');

  const elem = options['element']
  const html = '<' + elem + ' ' + flatatt + '>' + colortag.name + '</' + elem + '>';
  return $(html);
}

function django_colortag_choice() {
	jQuery(this).replaceInputsWithMultiStateButtons({
		groupClass: 'colortag-container',
		buttonClass: '',
		nocolor: true,
		buttonSetup: function(input, button) {
			button.css('--colortag-color', input.data('background'));
		},
	});
}

function selectNextOption(e, increment = 1) {
  const group = e.currentTarget;
  const child_inputs = group.querySelectorAll("input");
  const checked_i = Array.prototype.findIndex.call(child_inputs, (elem) => elem.checked);
  const next = child_inputs[(checked_i + increment) % 3];
  next.checked = true;
  next.focus({ focusVisible: (e.type == "keydown")});
  e.preventDefault();
}

window.addEventListener("load", (event) => {
  /* Set up toggling between colortag include-exclude states */
  const groups = document.querySelectorAll(".colortag-inc-exc");
  for (const g of groups) {
    g.addEventListener('click', selectNextOption);
    g.addEventListener('keydown', function(e) {
      if(e.keyCode == 13 || e.keyCode == 32) {
          selectNextOption(e);
      }
   });
   g.addEventListener('contextmenu', (e) => selectNextOption(e, 2));
  }

  $('[data-bs-toggle="popover"]').popover();
});
