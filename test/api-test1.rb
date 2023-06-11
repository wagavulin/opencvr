#!/usr/bin/env ruby

$:.unshift(File.dirname(__FILE__) + "/..")
require 'numo/narray'
require 'cv2'
require 'test/unit'

class ApiTest < Test::Unit::TestCase
  def test_version
    assert_equal(CV2::getVersionMajor.class, Integer)
    assert_equal(CV2::getVersionMinor.class, Integer)
    assert_equal(CV2::getVersionRevision.class, Integer)
    assert_equal(CV2::getVersionString.class, String)
  end

  def test_rectangle
    img0 = Numo::UInt8.zeros(400, 600, 3)
    img1 = img0.clone()
    CV2::rectangle(img1, [100,100], [200, 200], [255,0,0])
    CV2::rectangle(img1, [300,100, 100, 100], [0,0,255])
    assert_not_equal(img0, img1)
  end

  def test_putText
      img0 = Numo::UInt8.zeros(600, 800, 3)
      img0[0..-1, 0..-1, 0] = 255
      img1 = img0
      img2 = img0.clone()
      CV2::putText(img0, "Hello", [100, 100], CV2::FONT_HERSHEY_PLAIN, 5, [255,255,255], 2)
      CV2::rectangle(img0, [50,50], [150, 100], [255,255,255])
      assert_equal(img0, img1)
      assert_not_equal(img0, img2)
  end

  def test_hconcat # test of vector_Mat
    img0 = Numo::UInt8.zeros(200, 200, 3)
    img0[0..-1, 0..-1, 0] = 255
    img1 = Numo::UInt8.zeros(200, 200, 3)
    img1[0..-1, 0..-1, 1] = 255
    img2 = CV2::hconcat([img0, img1])
    assert_equal(img2.shape, [200, 400, 3])
  end
end
