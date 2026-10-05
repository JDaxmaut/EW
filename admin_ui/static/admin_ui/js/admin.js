/* Мелочи UX админки: примеры в пустых полях тура. */
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    // Плейсхолдеры-примеры, если поле пустое. Идентификаторы — реальные
    // поля trips.Destination, чтобы подсказки не врали.
    var examples = {
      summary: "Например: Дикий песок между скалами, 2,5 ч в пути",
      price_from: "Например: 1 900",
      subtitle: "Например: Дикий пляж в сосновом бору",
      travel_time: "Например: 2,5 ч",
      parking: "Например: платная, 300 ₽/день",
    };
    Object.keys(examples).forEach(function (field) {
      var el = document.getElementById("id_" + field);
      if (el && !el.placeholder) el.placeholder = examples[field];
    });
  });
})();
