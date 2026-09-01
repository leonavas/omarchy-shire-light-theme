-- Shipping hyprland.lua replaces the file Omarchy generates from
-- default/themed/hyprland.lua.tpl, so the border gradient from colors.toml is
-- restated here by hand. Keep the two in sync if you edit colors.toml.
local active_border_color = { colors = { "rgba(a3c46eee)", "rgba(e0b44fee)" }, angle = 45 }
local inactive_border_color = "rgba(46523aaa)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  -- Hobbit holes are round. rounding_power 3 makes a superellipse rather than
  -- a plain arc, so corners bulge slightly — softer, less machined.
  -- Solitude uses 6/3; the Shire wants more.
  decoration = {
    rounding = 10,
    rounding_power = 3,
  },
})
