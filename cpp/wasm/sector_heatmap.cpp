#include <cmath>
#include <string>
#include <vector>
#include <sstream>
#include <emscripten/bind.h>

namespace warroom {

static const std::vector<std::string> kSectorPalette = {
    "#0B3D91", "#1E90FF", "#3CB371", "#FFD700", "#FF8C00",
    "#8A2BE2", "#DC143C", "#2F4F4F", "#708090", "#B22222", "#4B0082"
};

std::vector<double> safe_zscore(const std::vector<double>& values) {
    std::vector<double> result;
    if (values.empty()) return result;

    double sum = 0.0;
    for (double v : values) {
        if (std::isnan(v) || std::isinf(v)) continue;
        sum += v;
    }
    double mean = sum / values.size();

    double variance = 0.0;
    for (double v : values) {
        if (std::isnan(v) || std::isinf(v)) continue;
        double diff = v - mean;
        variance += diff * diff;
    }
    double stddev = std::sqrt(variance / values.size());
    if (stddev <= 0.0) stddev = 1.0;

    result.reserve(values.size());
    for (double v : values) {
        if (std::isnan(v) || std::isinf(v)) {
            result.push_back(0.0);
            continue;
        }
        result.push_back((v - mean) / stddev);
    }

    return result;
}

std::string json_heatmap_data(const std::vector<double>& scores, const std::vector<std::string>& names) {
    std::ostringstream out;
    out << "{\"sectors\": [";
    size_t n = std::min(scores.size(), names.size());
    for (size_t i = 0; i < n; ++i) {
        double value = scores[i];
        std::string color = kSectorPalette[i % kSectorPalette.size()];
        out << "{\"name\": \"" << names[i] << "\", \"z\": " << value
            << ", \"color\": \"" << color << "\"}";
        if (i + 1 < n) out << ",";
    }
    out << "]}";
    return out.str();
}

std::string build_sector_heatmap(const std::vector<double>& raw_values) {
    std::vector<std::string> sector_names = {"XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"};
    std::vector<double> z = safe_zscore(raw_values);
    return json_heatmap_data(z, sector_names);
}

std::string format_money(double value) {
    std::ostringstream out;
    out.precision(2);
    out << std::fixed << "$" << value;
    return out.str();
}

std::string build_trade_ticket(const std::vector<std::string>& tickers,
                               const std::vector<double>& weights,
                               double portfolio_value) {
    if (tickers.size() != weights.size()) return "{}";
    std::ostringstream out;
    out << "{\"orders\": [";
    for (size_t i = 0; i < tickers.size(); ++i) {
        double allocation = weights[i] * portfolio_value;
        out << "{\"ticker\": \"" << tickers[i] << "\", \"targetValue\": \""
            << format_money(allocation) << "\", \"weight\": \"" << (weights[i] * 100.0)
            << "%\"}";
        if (i + 1 < tickers.size()) out << ",";
    }
    out << "]}";
    return out.str();
}

EMSCRIPTEN_BINDINGS(warroom_module) {
    emscripten::function("build_sector_heatmap", &build_sector_heatmap);
    emscripten::function("build_trade_ticket", &build_trade_ticket);
    emscripten::function("format_money", &format_money);
}

} // namespace warroom
