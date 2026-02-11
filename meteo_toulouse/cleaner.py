"""
Factory Pattern: Transforme les donnees brutes en objets WeatherRecord.

Detecte les differents formats de champs meteo et normalise les donnees.
"""

from __future__ import annotations

from meteo_toulouse.config import JSONLike
from meteo_toulouse.utils import norm, parse_datetime_any
from meteo_toulouse.models import WeatherRecord


class BasicCleaner:
    """
    Factory Pattern: Transforme les donnees brutes en objets WeatherRecord.

    Detecte les differents formats de champs meteo et normalise les donnees.
    """

    TEMP_KEYS = ["temperature", "temp", "temp_c", "tair", "temperature_c", "t", "tc"]
    HUM_KEYS = ["humidity", "humidite", "hum", "rh", "hr", "humidite_rel", "hum_rel"]
    P_KEYS = ["pressure", "pression", "press_hpa", "pression_hpa", "p", "pa", "p_hpa"]
    WIND_S_KEYS = ["wind_speed", "wind", "vitesse_vent", "ff", "ff10", "vent_ms", "vent_vitesse"]
    WIND_D_KEYS = ["wind_dir", "wind_direction", "dd", "dir_vent", "direction_vent"]
    RAIN_KEYS = ["rain", "pluie", "precipitation", "precipitations", "rr", "rr1", "rr24"]
    TS_PREF = ["date_observation", "date_mesure", "date_heure", "date", "datetime", "timestamp", "heure", "time"]

    def _get_first(self, data: JSONLike, keys: list[str]) -> object | None:
        """Cherche la premiere cle correspondante dans les donnees."""
        keys_norm = [norm(k) for k in data.keys()]
        mapping = {kn: k for k, kn in zip(data.keys(), keys_norm)}
        for kk in keys:
            kkn = norm(kk)
            if kkn in mapping:
                return data[mapping[kkn]]
        for kk in keys:
            kkn = norm(kk)
            for kn, orig in mapping.items():
                if kkn in kn:
                    return data[orig]
        return None

    def _to_float(self, x: object | None) -> float | None:
        """Convertit une valeur en float."""
        if x is None or x == "":
            return None
        try:
            return float(str(x).replace(",", "."))
        except ValueError:
            return None

    def clean(self, raw: JSONLike, station_id: str) -> WeatherRecord:
        """
        Transforme des donnees brutes en WeatherRecord.

        Args:
            raw: Donnees brutes de l'API.
            station_id: ID de la station source.

        Returns:
            WeatherRecord normalise.
        """
        ts_raw = self._get_first(raw, self.TS_PREF)
        ts = parse_datetime_any(ts_raw)

        t = self._to_float(self._get_first(raw, self.TEMP_KEYS))
        hum = self._to_float(self._get_first(raw, self.HUM_KEYS))
        p = self._to_float(self._get_first(raw, self.P_KEYS))
        ws = self._to_float(self._get_first(raw, self.WIND_S_KEYS))
        wd = self._to_float(self._get_first(raw, self.WIND_D_KEYS))
        rr = self._to_float(self._get_first(raw, self.RAIN_KEYS))

        return WeatherRecord(
            station_id=station_id,
            timestamp=ts,
            temperature_c=t,
            humidity_pct=hum,
            pressure_hpa=p,
            wind_speed_ms=ws,
            wind_dir_deg=wd,
            rain_mm=rr,
            raw=raw,
        )
