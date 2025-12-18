#include "desktop/desktop.h"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <chrono>
#include <thread>

TEST(Desktop, visible_desktop_start_and_stop) {
  std::unique_ptr<Desktop> desktop = Desktop::create(640, 480, true);
  for (int i = 0; i < 20; ++i) {
    auto f = desktop->get_frame();
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
  }
  desktop.reset();

  desktop = Desktop::create(640, 480, true);

  for (int i = 0; i < 20; ++i) {
    auto f = desktop->get_frame();
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
  }
}
