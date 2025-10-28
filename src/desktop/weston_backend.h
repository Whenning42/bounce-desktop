#ifndef DESKTOP_WESTON_BACKEND_H_
#define DESKTOP_WESTON_BACKEND_H_

#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "process/process.h"
#include "third_party/status/status_or.h"

class WestonBackend {
 public:
  static StatusOr<std::unique_ptr<WestonBackend>> start_server(
      int32_t port_offset, int32_t width, int32_t height);

  int port() { return port_; }

  // Returns a map holding the  display env vars callers can use to launch GUI
  // apps on this desktop. Specifically the returned env var map will include
  // "DISPLAY" and "WAYLAND_DISPLAY" env vars.
  const std::unordered_map<std::string, std::string>& get_desktop_env() const {
    return desktop_env_;
  }

 private:
  WestonBackend(int port, Process&& weston,
                std::unordered_map<std::string, std::string>&& desktop_env)
      : port_(port),
        weston_(std::move(weston)),
        desktop_env_(std::move(desktop_env)) {}

  int port_;
  Process weston_;
  std::unordered_map<std::string, std::string> desktop_env_;
};

#endif  // DESKTOP_WESTON_BACKEND_H_
