import rclpy
import time
from std_msgs.msg import Int8
from std_msgs.msg import Bool
from raspike_uros_msg.msg import MotorSpeedMessage        #motor speed
from raspike_uros_msg.msg import MotorResetMessage             #reset count
from raspike_uros_msg.msg import SpikeDevStatusMessage
from raspike_uros_msg.msg import ButtonStatusMessage
from raspike_uros_msg.msg import SpikePowerStatusMessage
from rclpy.node import Node
from rclpy.qos import QoSProfile
'''
global white_brightness
global brack_brightness
global target_brightness
global kp
global kd
global ki
global left_edge
global right_edge
global bace_speed
'''

white_brightness = 74
brack_brightness = 4
left_edge = -1
right_edge = 1

kp = 0.59
kd = 0.04
ki = 0.0
bace_speed = 40

cnt = 0


# サブスクライバーノード
class linetracerNode(Node):
    # 初期化
    def __init__(self):
        super().__init__("lt_sample_node")

        qos_profile = QoSProfile(depth=10, reliability=2)

        self.is_start = False
        self.steering_amount = 0
        # 受信メッセージ
        self.rev_color_mode = 0
        self.rev_color_sensor_ambient = 0
        self.rev_color_sensor_color = 0
        self.rev_color_sensor_refrection = 0
        self.rev_color_sensor_r = 0
        self.rev_color_sensor_g = 0
        self.rev_color_sensor_b = 0
        self.rev_ultrasonic_mode = 0
        self.rev_ultrasonic_val = 0
        self.rev_arm_cnt = 0
        self.rev_right_cnt = 0
        self.rev_left_cnt = 0
        self.rev_x_ang_vel = 0.0
        self.rev_button_val = 0
        self.rev_hub_volt = 0
        self.rev_hub_current = 0
        # 送信メッセージ
        self.send_arm_speed = 0
        self.send_right_speed = 0
        self.send_left_speed = 0
        self.send_is_arm_reset_cnt = False
        self.send_is_right_reset_cnt = False
        self.send_is_left_reset_cnt = False
        self.send_send_ultrasonic_mode = 0
        self.send_is_imu_init = False
        self.send_color_mode = 0
        # line_trace_on_tick
        self.is_rev_reflection = False
        self.is_rev_color_code = False
        self.diff = [0, 0]
        self.pre_i_val = 0

        # パブリッシャーの生成
        self.motor_speed_publisher = self.create_publisher(MotorSpeedMessage, "wheel_motor_speeds", qos_profile)
        self.motor_reset_count_publisher = self.create_publisher(MotorResetMessage, "motor_reset_count", 10)
        self.color_mode_publisher = self.create_publisher(Int8, "color_sensor_mode", qos_profile)
        self.ultrasonic_mode_publisher = self.create_publisher(Int8, "ultrasonic_sensor_mode", 10)
        self.imu_init_publisher = self.create_publisher(Bool, "imu_init", 10)
        # タイマーの生成
        self.timer_callback = self.create_timer(0.01, self.timer_on_tick)                           #wheel_speed
        self.line_trace_callback = self.create_timer(0.01, self.line_trace_on_tick)
        # サブスクライバーの生成
        self.dev_status_subscription = self.create_subscription(
            SpikeDevStatusMessage, "spike_device_status", self.dev_status_on_subscribe, qos_profile)
        self.button_status_subscription = self.create_subscription(
            ButtonStatusMessage, "spike_button_status", self.button_status_on_subscribe, qos_profile)
        self.hub_status_subscription = self.create_subscription(
            SpikePowerStatusMessage, "spike_power_status", self.hub_status_on_subscribe, qos_profile)
        
        self.get_logger().info("line tracer node init")

    # reflettionを取得
    def get_reflection(self):
        if self.send_color_mode != 3:
            send_color_mode = 3
            color_mode = Int8()
            color_mode.data = send_color_mode
            self.color_mode_publisher.publish(color_mode)

        if self.rev_color_mode == 3:
            self.is_rev_reflection =  True
            
    def steering_amount_calculation(self):
        target_brightness = (white_brightness - brack_brightness) / 2
        
        diff_brightness = target_brightness - self.rev_color_sensor_refrection
        delta_t = 10

        self.diff[1] = self.diff[0]
        self.diff[0] = int(diff_brightness)

        p_val = diff_brightness
        i_val = self.pre_i_val + (self.diff[0] + self.diff[1]) * delta_t / 2
        d_val = int((self.diff[0] - self.diff[1]) / 1)

        self.steering_amount = (kp * p_val) + (kd * d_val) + (ki * i_val)

    def motor_drive_control(self):
        self.send_left_speed = int(bace_speed + (self.steering_amount * left_edge))
        self.send_right_speed = int(bace_speed - (self.steering_amount * left_edge))

        if self.send_left_speed > 80:
            self.send_left_speed =80
        if self.send_left_speed < -80:
            self.send_left_speed =-80
        if self.send_right_speed >80:
            self.send_right_speed = 80
        if self.send_right_speed  < -80:
            self.send_right_speed = -80

    def line_trace_on_tick(self):

        if self.rev_button_val == 16:
            self.is_start = True
        if self.is_start == False:
            return

        self.get_reflection()       #reflection値を取得
        if self.is_rev_reflection == False:     #reflection値が更新するまで待機
            return

        self.steering_amount_calculation()
        self.motor_drive_control()

        # 初期状態に戻す
        self.is_rev_reflection = False
        self.is_rev_color_code == False
        self.rev_color_mode = 0

    def timer_on_tick(self):
        # メッセージの生成
        motor_speed = MotorSpeedMessage()

        motor_speed.right_motor_speed = self.send_right_speed
        motor_speed.left_motor_speed = self.send_left_speed
        motor_speed.arm_motor_speed = self.send_arm_speed
        # メッセージのパブリッシュ
        self.motor_speed_publisher.publish(motor_speed)


    # サブスクライバー　コールバック
    def dev_status_on_subscribe(self, devise_status):

        self.rev_color_mode = devise_status.color_mode_id
        if self.rev_color_mode == 1:
            self.rev_color_sensor_ambient = devise_status.color_sensor_value_1
        elif self.rev_color_mode == 2:
            self.rev_color_sensor_color = devise_status.color_sensor_value_1
        elif self.rev_color_mode == 3:
            self.rev_color_sensor_refrection = devise_status.color_sensor_value_1
        elif self.rev_color_mode == 4:
            self.rev_color_sensor_r = devise_status.color_sensor_value_1
            self.rev_color_sensor_g = devise_status.color_sensor_value_2
            self.rev_color_sensor_b = devise_status.color_sensor_value_3

        self.rev_ultrasonic_mode = devise_status.ultrasonic_mode_id
        self.rev_ultrasonic_val = devise_status.ultrasonic_sensor
        self.rev_arm_cnt = devise_status.arm_count
        self.rev_right_cnt = devise_status.right_count
        self.rev_left_cnt = devise_status.left_count
        self.rev_x_ang_vel = devise_status.gyro_sensor
        
    def button_status_on_subscribe(self, button_status):
        self.get_logger().info("touch_sensor : " + str(button_status.touch_sensor))
        self.get_logger().info("button : " + str(button_status.button))

        self.rev_button_val = button_status.button

    def hub_status_on_subscribe(self, hub_status):

        self.rev_hub_volt = hub_status.voltage
        self.rev_hub_current = hub_status.current


# メイン
def main(args=None):
    # ROS通信の初期化
    rclpy.init(args=args)

    # ノードの生成
    node = linetracerNode()

    # ノード終了まで待機
    rclpy.spin(node)

    # ノードの破棄
    node.destroy_node()

    # RCLのシャットダウン
    rclpy.shutdown()


if __name__ == "__main__":
    main()
