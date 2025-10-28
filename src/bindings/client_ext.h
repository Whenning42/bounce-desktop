#ifndef BINDINGS_CLIENT_EXT_H_
#define BINDINGS_CLIENT_EXT_H_

#include <memory>
#include <string>
#include <unordered_map>

#include "desktop/client.h"
#include "desktop/weston_backend.h"
#include "third_party/status/status_or.h"

class Desktop : public BounceDeskClient {
 public:
  static std::unique_ptr<Desktop> create(int32_t width, int32_t height);

  // Returns the backend's desktop env vars. The comment in weston_backend.h
  // has the details.
  const std::unordered_map<std::string, std::string>& get_desktop_env() const {
    return backend_->get_desktop_env();
  }

 private:
  Desktop() {};

  // Hide BounceDeskClient methods that don't belong in Desktop's interface.
  using BounceDeskClient::connect;
  using BounceDeskClient::get_frame_impl;
  using BounceDeskClient::resize;

  std::unique_ptr<WestonBackend> backend_;
};

#endif  // BINDINGS_CLIENT_EXT_H_
