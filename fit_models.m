%% Create direct relationship model to fit bulb lux values to 0-250 range
% This part of the code fits (extrapolates) lux values from 0-100 to 0-250
% The 0-100 lux restriction is forced in the python file sensor_data.py
% 100 was chosen as the max lux because it is approximately the amount of 
% natural light in the room at the brightest day
% It is extrapolated to 0-250 because that is approximately the brightness
% value range of the actual Philips Hue Bulb

clear all, close all

brightness = zeros(1,26);
brightness(1) = 0;

% create 0-250 range in intervals of 10
for k=2:26
    brightness(k) = brightness(k-1) + 10;
end 

lux = zeros(1,26);
lux(1) = 0;

% create 0-100 range in intervals of 4
for j=2:26
    lux(j) = lux(j-1) + 4;
end

% transpose each vector to create column vectors for fit_mdl requirement
lux = lux'; 
brightness = brightness';

% curve of best fit that matches lux values to brightness values
fit_mdl = fit(lux,brightness,'poly1') 

figure('DefaultAxesFontSize',13)
plot(lux,brightness,'d')
hold on
plot(fit_mdl)
hold off
grid on
ylim([0 250])
title('Interpolated Light Sensor Values','fontsize',13)
xlabel('Lux Values','fontsize',13)
ylabel('Brightness Values','fontsize',13)

%% Create inverse relationship model for bulb brightness and room light levels
% This part of the code creates the inverse of the above model. This will
% be used as the actual brightness value being set. Simply, the bulb
% will get brighter if the room is darker and vice versa. 

brightness2 = flipud(brightness)

fit_mdl2 = fit(lux,brightness2,'poly1');

figure('DefaultAxesFontSize',13)
plot(lux,brightness2,'d')
hold on
plot(fit_mdl2)
hold off
grid on
ylim([0 250])
title('Inverse Model for Brightness Change','fontsize',13)
xlabel('Lux Values','fontsize',13)
ylabel('Brightness Values','fontsize',13)
