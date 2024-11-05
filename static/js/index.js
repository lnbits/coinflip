window.app = Vue.createApp({
  el: "#vue",
  mixins: [windowMixin],
  data() {
    return {
      formDialogCoinflip: {
        show: false,
        fixedAmount: true,
        data: {
          number_of_players: 2,
          buy_in: 1000,
          wallet: null,
        },
      },
      coinflipSettings: {
        id: "",
        enabled: false,
        haircut: 0,
        max_players: 2,
        max_bet: 1000,
        wallet_id: null,
      },
    };
  },
  methods: {
    async saveCoinflipSettings() {
      let settings = {
        enabled: this.coinflipSettings.enabled,
        haircut: this.coinflipSettings.haircut,
        max_players: this.coinflipSettings.max_players,
        max_bet: this.coinflipSettings.max_bet,
      };
      let method = "";
      if (this.coinflipSettings.id != null) {
        settings.id = this.coinflipSettings.id;
        settings.wallet_id = this.coinflipSettings.wallet_id;
        settings.user_id = this.g.user.id;
        method = "PUT";
      } else {
        method = "POST";
      }
      await LNbits.api
        .request(
          method,
          "/coinflip/api/v1/coinflip/settings",
          this.g.user.wallets[0].adminkey,
          settings,
        )
        .then((response) => {
          this.coinflipSettings = response.data;
          Quasar.Notify.create({
            type: "positive",
            message: "Coinflip settings saved!",
          });
        })
        .catch((err) => {
          LNbits.utils.notifyApiError(err);
        });
    },
    async getCoinflipSettings() {
      await LNbits.api
        .request(
          "GET",
          "/coinflip/api/v1/coinflip/settings",
          this.g.user.wallets[0].adminkey,
        )
        .then((response) => {
          this.coinflipSettings.id = response.data.id;
          this.coinflipSettings.enabled = response.data.enabled;
          this.coinflipSettings.haircut = response.data.haircut;
          this.coinflipSettings.max_players = response.data.max_players;
          this.coinflipSettings.max_bet = response.data.max_bet;
          this.coinflipSettings.wallet_id = response.data.wallet_id;
        })
        .catch((err) => {
          LNbits.utils.notifyApiError(err);
        });
    },
    async createGame() {
      const wallet = _.findWhere(this.g.user.wallets, {
        id: this.coinflipSettings.wallet_id,
      });
      const data = {
        name: this.formDialogCoinflip.data.title,
        number_of_players: parseInt(
          this.formDialogCoinflip.data.number_of_players,
        ),
        buy_in: parseInt(this.formDialogCoinflip.data.buy_in),
        settings_id: this.coinflipSettings.id,
      };
      if (data.buy_in > this.coinflipSettings.max_bet) {
        Quasar.Notify.create({
          type: "negative",
          message: `Max bet is ${this.coinflipSettings.max_bet}`,
        });
        return;
      }
      if (
        this.formDialogCoinflip.number_of_players >
        this.coinflipSettings.max_players
      ) {
        Quasar.Notify.create({
          type: "negative",
          message: `Max players is ${this.coinflipSettings.max_players}`,
        });
        return;
      }
      try {
        const response = await LNbits.api.request(
          "POST",
          "/coinflip/api/v1/coinflip",
          wallet.inkey,
          data,
        );
        if (response.data) {
          this.activeGame = true;

          const url = new URL(window.location);
          url.pathname = `/coinflip/coinflip/${this.coinflipSettings.id}/${response.data}`;
          window.open(url);
        }
      } catch (error) {
        LNbits.utils.notifyApiError(error);
      }
    },
  },
  async created() {
    // CHECK COINFLIP SETTINGS
    await this.getCoinflipSettings();
  },
});
