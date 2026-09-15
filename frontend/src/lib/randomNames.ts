/**
 * Names for anyone who would rather not type one.
 *
 * Shaped like the handles Reddit offers on sign-up -- adjective, noun, number
 * -- because that reads as a name without being anyone's. A fixed list rather
 * than parts combined at random: a hundred is more than enough for a session
 * that lasts a day, and a list can be read to check nothing in it is unkind.
 *
 * Collisions do not matter. A session id is its name plus a timestamp plus a
 * random suffix, so two people called Sunny_Otter_4417 still get their own
 * session and cannot see each other's databases.
 */
export const RANDOM_NAMES: readonly string[] = [
  'Brave_Ember_1421', 'Brave_Ocelot_2030', 'Brave_Prairie_1516',
  'Calm_Fjord_6523', 'Calm_Iris_1661', 'Calm_Moss_6490',
  'Cheerful_Pepper_4958', 'Cheerful_Valley_4965', 'Cosmic_Ginger_7385',
  'Crisp_Cricket_2529', 'Curious_Salmon_9422', 'Dusty_Quokka_8944',
  'Eager_Kettle_1180', 'Electric_Fjord_3772', 'Electric_Lilac_5174',
  'Electric_Radish_8673', 'Fancy_Heron_1694', 'Fancy_Thistle_9338',
  'Fearless_Spruce_7572', 'Fearless_Summit_9107', 'Fearless_Walnut_4165',
  'Fluffy_Galaxy_3233', 'Frosty_Pigeon_3933', 'Frosty_Rabbit_6635',
  'Gentle_Moss_1808', 'Golden_Ocelot_3436', 'Golden_Yak_1436',
  'Happy_Muffin_2009', 'Hidden_Bagel_946', 'Hidden_Lilac_667',
  'Hidden_Meadow_3327', 'Hidden_Raven_1966', 'Honest_Quokka_6942',
  'Humble_Puffin_2250', 'Humble_Spruce_7691', 'Humble_Toucan_3459',
  'Icy_Comet_9207', 'Icy_Hazel_9623', 'Icy_Lilac_220',
  'Icy_Moss_8098', 'Icy_Radish_7947', 'Jolly_Kettle_2746',
  'Jolly_Lemur_1231', 'Jolly_Wombat_5992', 'Lucky_Radish_2580',
  'Lucky_Summit_7567', 'Lucky_Walnut_312', 'Mellow_Ferret_7350',
  'Mellow_Walrus_9386', 'Mighty_Cactus_4913', 'Mighty_Falcon_3372',
  'Mighty_Galaxy_2471', 'Mighty_Prairie_4686', 'Mighty_Salmon_6068',
  'Nimble_Anchor_6512', 'Nimble_Squid_738', 'Noble_Ember_428',
  'Noble_Toucan_6873', 'Noble_Valley_6125', 'Plucky_Reef_7495',
  'Plucky_Sage_2759', 'Plucky_Spruce_7121', 'Polite_Willow_2062',
  'Quick_Ember_9176', 'Quiet_Bramble_3960', 'Quiet_Fern_2644',
  'Quiet_Velvet_3772', 'Rapid_Rabbit_2448', 'Restless_Coral_3299',
  'Restless_Puffin_8750', 'Restless_Squid_4161', 'Rusty_Acorn_5458',
  'Sandy_Badger_6634', 'Sandy_Squid_8194', 'Sharp_Dolphin_6969',
  'Smooth_Marble_7818', 'Smooth_Pigeon_4513', 'Smooth_Tundra_9764',
  'Solid_Lynx_3223', 'Solid_Squid_8417', 'Solid_Walnut_8895',
  'Spicy_Kettle_8612', 'Spicy_Summit_2915', 'Sturdy_Meadow_408',
  'Sturdy_Puffin_7425', 'Sunny_Bagel_5202', 'Sunny_Moss_3352',
  'Sunny_Sage_6986', 'Sunny_Velvet_4304', 'Tidy_Sage_1968',
  'Tiny_Dolphin_7787', 'Tiny_Fern_4489', 'Tiny_Fjord_667',
  'Upbeat_Cactus_8164', 'Upbeat_Otter_902', 'Vivid_Galaxy_15',
  'Vivid_Lemur_7597', 'Vivid_Penguin_2139', 'Wise_Quartz_6152',
  'Zesty_Zebra_6629',
];

/**
 * A name from the list, never the one already showing.
 *
 * Clicking again must visibly do something; handing back the same name looks
 * like a broken button.
 */
export function randomName(exclude?: string): string {
  const pool = exclude ? RANDOM_NAMES.filter((name) => name !== exclude) : RANDOM_NAMES;
  const choices = pool.length > 0 ? pool : RANDOM_NAMES;
  return choices[Math.floor(Math.random() * choices.length)] as string;
}
